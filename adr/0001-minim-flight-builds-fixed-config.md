# ADR-0001: Fly the Minim ESCs on one fixed firmware per pod

- **Status:** Accepted, not yet bench tested
- **Date:** 2026-11-26
- **Branch:** `hylight/minim-flight-fixed`, release `minim-flight-7.0.2`
- **Deciders:** Renan

## Context

The MFX airship flies five Minim ESCs (front, T1 to T4) driven by PX4 over UAVCAN
RawCommand in rpm mode, all on one CAN bus. The stock firmware (VESC 7.00 plus the
Custom 7.0.x commits) behaves like a consumer ESC: power button, shutdown broadcast,
one editable config copy in flash with a generic fallback, setup wizards. Three
problems followed.

**All five motors stopped in flight, twice (23 Nov 2026 L3, 24 Nov 2026 L2, the
second one a crash).** Same signature both days: one ESC drops to exactly 0 A, the
other four follow 0.2 to 0.4 s later, no fault code, all ESCs still alive on CAN, no
restart for 20 s while PX4 keeps ordering full rpm. The code path that matches is the
Minim smart switch (`hwconf/vesc/minim/hw_minim_core.c`, shutdown mode 2
TOGGLE_BUTTON_ONLY): the PSW pin both holds the power latch and is sampled as the
button. Every Minim is switched on by a jumper from BAT to PSW, so the pin reads
"pressed" all the time. After one "not pressed" reading the state machine arms, and
the next one runs the shutdown: release the motor, broadcast `CAN_PACKET_SHUTDOWN`,
ignore input for 20 s. Since 23 Nov the ESCs run CAN mode VESC_UAVCAN, so the other
four obeyed the broadcast. Before that, 50 single ESC stops since September lasted
10.2 s or 20.3 s each, the two lockout times of this code (6.06 and 7.00), always on
one board, and they ended when that board was replaced.

What makes the pin misread is not proven. The stop rate rises as the ESC input
voltage falls, but no fixed threshold predicts it, and there is no Minim schematic.
An adversarial review of the logs put this explanation at about 80 %, every
alternative under 5 %.

**Configs changed on their own.** On 23 Nov four ESCs reported Fares' config reset
flag (code 14) and flew in current mode instead of rpm mode. At boot a config that
fails its CRC is replaced by firmware defaults in RAM only, so the reset repeats at
every boot until someone writes the config again. Why the stored configs failed is
unknown (a layout change at the 19 Nov reflash, or a power loss during a write).

**Bad motor detections on the ship.** On 24 Nov three of the four rear ESCs carried a
flux linkage 19 to 41 % low (T1 0.001576, T2 and T4 0.002169, against 0.00268). T1
drew 18 % more current, hit its 29 A limit first and turned about 230 rpm under T4
at full order.

## Decision

We fly one firmware per pod with everything compiled in, and nothing on the ESC can
change it or stop the motor on its own. One tag, five build targets
(`minim_flight_front`, `minim_flight_t1` to `_t4`, all behind `HW_MINIM_FLIGHT`):

1. **Config compiled in.** CAN id, UAVCAN ESC index, motor direction, motor config
   and app config are constants. The stored config is never read and flash is never
   written (`conf_general.c`). Rear motor config from the T3 detection of 24 Nov
   (R 0.0942, L 49.3 uH, flux 0.00268), identical on T1 to T4. Front from the 23 Nov
   front file. App config as flown 24 Nov, with shutdown Always On and rpm mode.
2. **No self shutdown.** The power pin is driven high and never read as a button,
   both shutdown threads do nothing (`hw_minim_core.c`, `hwconf/shutdown.c`), the CAN
   shutdown is neither sent nor obeyed (`comm/comm_can.c`).
3. **Nothing touches a motor in use.** While any motor of the ship has a non zero
   order within 3 s, or this motor is not off, or turns above 300 ERPM, every VESC
   frame is dropped and only read only packets are answered on USB, UART and CAN
   (`hw_minim_flight_busy`, `comm/commands.c` `flight_packet_allowed`).
4. **Refused at all times:** config writes, motor commands other than UAVCAN
   RawCommand, detection, emergency stop, terminal, Lisp, upload to all, UAVCAN param
   set, RPMCommand. **Idle only:** firmware upload, reboot, UAVCAN restart.
5. **Zero release.** An exact 0 order held for 1 s releases the motor, so HFI stops
   hissing on the ground (`libcanard/canard_driver.c` `handle_esc_raw_command`). It
   replaces the Lisp script, which no longer starts.
6. **Self check.** Once per second each ESC compares its live config with the
   compiled one and reports a config fault code in the UAVCAN status when they differ.
7. **No battery voltage derating.** The battery cut sits at 10 / 8 V, below the 15 V
   undervoltage fault, so the 30 A input limit holds at any voltage
   (`hwconf/vesc/minim/mcconf_minim_flight_limits.h`). The pack relies on the PX4
   battery failsafe.
8. **Directions** (26 Nov): invert 1 on T1 and T4, 0 on front, T2, T3, with the
   phase wiring of that day. Target rule: T1 and T3 clockwise, T2 and T4 counter
   clockwise.

The bench targets `minim_back` and `minim_front` keep their behaviour.

## Alternatives considered

| Option | Why not |
|---|---|
| Config only: shutdown Always On and CAN mode UAVCAN on each ESC | Fixes the stop only as long as the stored config survives. A config reset brings back mode 2 and VESC_UAVCAN, which is what happened on 23 Nov. |
| Fares' baked defaults (Custom 7.0.0) as the fallback | They are the August long cable values (R 0.233, no HFI, cut 40.8 / 36 V) and keep the button and the editable config. A reset ESC would fly another tune. |
| Rewire the jumper as a soldered, glued link | Worth doing, but it only lowers the chance of a misread. The firmware would still shut down on one. |
| Fix the stale timer and keep the button | Keeps a code path that can stop a motor in flight on a pin nobody presses. |
| Redundant config copies in flash | Still lets a wrong config be written and kept. A fixed config removes the problem. |
| One branch per ESC | Five places to keep in step. One commit with five targets differs only in the pod header. |
| Allow terminal commands when idle | The command bodies were not audited; refusing them costs only the `faults` read out. |
| Keep the 34 / 30 V battery cut | It acts on each ESC's own input, so it cut the ESC further down the cable first. Renan wants full power at any voltage. |

## Consequences

- A config change needs a new build and a flash; it cannot be done in VESC Tool.
  Each binary fits only its pod. A T1 binary on the T3 ESC would run with the wrong
  id, index and direction: a ground actuator test per pod is the only check.
- After a fault the motor restarts 0.5 s later on the next order; after a CAN loss
  it freewheels after 1 s and restarts on the first order. No latch.
- After the 1 s zero release, the armed idle order (6 ERPM) leaves the motor off
  until 900 ERPM, as with the Lisp script.
- An ESC reset in flight runs the boot offset calibration with the propeller turning:
  at least 3.1 s without the motor and possibly wrong offsets. Same as stock.
- After a kill in flight, the idle only commands open 3 s later if the propeller
  turns slowly.
- No voltage protection on the ESC. The PX4 battery failsafe is the only guard.
- The terminal is refused, so `faults` cannot be read on the flight build.
- Lisp is still linked (about 37 kB); flash is 98.4 % full.
- PX4 raises an alert on the ESC config fault code but does not refuse to arm.
- The trigger of the pin misread is not proven. This decision closes the shutdown
  path whatever the trigger, but a different cause with the same signature would not
  be covered.

## How to check this is still true

- `fw_info` on each ESC shows the tag's commit; the release lists the SHA256 of each
  binary.
- `git grep -n HW_MINIM_FLIGHT` lists every place the flight behaviour differs.
- `git grep -n "MCCONF_M_INVERT_DIRECTION\|APPCONF_CONTROLLER_ID\|APPCONF_UAVCAN_ESC_INDEX" hwconf/vesc/minim/hw_minim_flight_*.h`
  gives the pod table.
- In a flight log: `esc_status` error count 0 on all five, and rpm = order x 2380
  below full order (rpm mode).
- Bench, not done yet: on a bridged board, step the supply from 46 to 30 V and flex
  the jumper: the stock firmware's `test_button` should flip, the flight build must
  never stop. Then 50 power cycles with the same config read back each time.

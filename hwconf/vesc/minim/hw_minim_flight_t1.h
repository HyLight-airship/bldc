/*
	Copyright 2026 Hylight

	This file is part of the VESC firmware.

	The VESC firmware is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The VESC firmware is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    */

#ifndef HW_MINIM_FLIGHT_T1_H_
#define HW_MINIM_FLIGHT_T1_H_

// Airship flight build for the rear bottom clockwise T1 (U8) pod. The whole motor and app config is
// compiled in and loaded at every boot; flash is never read or written for
// config (see conf_general.c). One binary per pod, so nothing is stored per unit.
// Decisions and evidence: adr/0001-minim-flight-builds-fixed-config.md

#define HW_MINIM
#define HW_MINIM_FLIGHT
#define HW_MINIM_FLIGHT_POD				"t1"

// Per pod identity, as flown on 24 Nov 2026.
#define APPCONF_CONTROLLER_ID			3
#define APPCONF_UAVCAN_ESC_INDEX		1

// Direction flag as flown on 24 Nov 2026 with that day's phase wiring. The
// spin direction depends on the phase wire order as well as on this flag, so
// it must be confirmed by a spin test on the final harness before flight.
#define MCCONF_M_INVERT_DIRECTION		1

// Limits shared by the five flight builds, set before the motor config so
// they win over its values.
#include "mcconf_minim_flight_limits.h"

// Shared motor config for this pod type, then the shared app config. Both are
// #ifndef guarded, so the per pod values above win.
#include "mcconf_minim_flight_back.h"
#include "appconf_minim_flight.h"

#include "hw_minim_core.h"

#endif /* HW_MINIM_FLIGHT_T1_H_ */

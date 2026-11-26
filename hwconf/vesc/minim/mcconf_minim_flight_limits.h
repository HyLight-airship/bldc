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

#ifndef MCCONF_MINIM_FLIGHT_LIMITS_H_
#define MCCONF_MINIM_FLIGHT_LIMITS_H_

// Limits shared by the five flight builds. Included before the motor config,
// whose values are #ifndef guarded, so these win and a motor config generated
// again from a VESC Tool file cannot bring another value back.

// No battery voltage derating: the input current limit keeps its full value at
// any input voltage. Both thresholds sit below the under voltage fault
// (MCCONF_L_MIN_VOLTAGE), so the cut in mc_interface.c never acts. The pack is
// protected by the autopilot's battery failsafe only.
// See adr/0001-minim-flight-builds-fixed-config.md, decision 7.
#define MCCONF_L_BATTERY_CUT_START		10.0
#define MCCONF_L_BATTERY_CUT_END		8.0

#endif /* MCCONF_MINIM_FLIGHT_LIMITS_H_ */

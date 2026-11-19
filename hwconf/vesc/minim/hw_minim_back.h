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

#ifndef HW_MINIM_BACK_H_
#define HW_MINIM_BACK_H_

#define HW_MINIM

// Bake the back-motor (U8) flight config as the reset defaults. Included
// before hw_minim_core.h so these #ifndef-guarded values win over the generic
// hardware overrides and the global mcconf defaults.
#include "mcconf_minim_back.h"

#include "hw_minim_core.h"

#endif /* HW_MINIM_BACK_H_ */

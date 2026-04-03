# Copyright (C) 2025 EnipOIXth (Glenn Maidon)
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


bl_info = {
    "name": "Pinerig Hand Macro",
    "author": "EnipOIXth",
    "version": (0, 1, 1), # Addon version.
    "blender": (4, 1, 0), # Minimum supported Blender version.
    "description": "Generate a hand macro bone and action constraints for FK finger rigs",
    "category": "Rigging",
    "location": "View3D > Sidebar > Hand Macro",
    # Web site links:
    #"link": "https://github.com/", # Github link.
    #"doc_url": "https://", # Documentation link.
    #"tracker_url": "https://",
    #"warning": "Warning message, e.g. the set is experimental.",
}


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


import bpy
import sys
import importlib
import addon_utils
from bpy.types import AddonPreferences
from typing import Optional


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


ADDON_NAME = __package__.split(".")[0]


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###


def blender_version_at_least(min_version: tuple[int]) -> bool:
    """Check if current Blender version meets minimum requirements."""
    return bpy.app.version >= min_version


def get_addon_prefs() -> AddonPreferences:
    """ Helper to retreive the addon preferences."""
    return bpy.context.preferences.addons[ADDON_NAME].preferences


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#------------ Submodule loading system ------------#
####################################################


if "loaded_submodules" not in globals():
    loaded_submodules = []


submodules = (
    'utils',
    'main',
)


def register_submodules():
    loaded_submodules[:] = [importlib.import_module(__name__ + '.' + name) for name in submodules]
    for mod in loaded_submodules:
        if hasattr(mod, "register"):
            mod.register()


def unregister_submodules():
    for mod in reversed(loaded_submodules):
        if hasattr(mod, "unregister"):
            mod.unregister()
    loaded_submodules.clear()


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#------------- Submodules Reloading ---------------#
####################################################


def reload_submodules():
    """
    Reload all modules belonging to this addon package.
    Reloads children before parents.
    """
    prefix = ADDON_NAME + "." 
    modules = [ name for name in sys.modules if name.startswith(prefix) ]

    # Reload parents first
    for name in sorted(modules, key=lambda n: n.count("."), reverse=False):
        try:
            mod = importlib.reload(sys.modules[name])
            #print(f"[Pinerig] Reloaded: {name}")
            #if hasattr(mod, "reload"):
                #mod.reload()
        except Exception as e:
            print(f"[Pinerig] Failed to reload {name}: {e}")


_needs_reload : bool = "bpy" in locals()
if _needs_reload:
    reload_submodules()


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#--------------- Class registration ---------------#
####################################################


classes = ()


def register_classes():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister_classes():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


###--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------###
####################################################
#------------------ REGISTRATION ------------------#
####################################################


def register():
    register_submodules()
    register_classes()


def unregister():
    unregister_classes()
    unregister_submodules()


if __name__ == "__main__":
    register()


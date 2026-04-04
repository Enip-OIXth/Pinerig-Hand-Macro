# Pinerig-Hand-Macro

Blender extension that generates a hand macro bone and action constraints for FK finger on any rig (Rigify, ARP, Custom...).

Compatible with Blender 4.1 to 5.2





**Installation:**

Install it like any other addon. 

You'll find the hand macro panel in the 3D view's N-panel when you have an armature selected in pose mode.



**How to use:**

Select your hand bone (most likely IK but you can also work with FK/ORG/DEF hand bone). 

Create a new hand system, set the finger flexion axis.

Use the auto-detect FK fingers feature. If it didn't work, you'll have to add the finger data manually.

Symmetrize the data, and then hit generate hand macro.

It will procedurally generate actions and keyframes that you can tweak to your liking.

You can reposition the hand macro bone in edit mode and tweak it as you wish.



Beware that re-generating may wreck your modifications.



**Gotchas:**

* Fingers are bent in funny ways after playing with the hand macro: Either you haven't set the correct flexion axis, or one of your fingers needs to have it's roll tweaked in edit mode.,
* How do I tweak poses? -> You change your timeline to a Dope sheet, set the editor to Action editor and then you'll find actions in the action dropdown. Final poses are set at frame 10.You can also set intermediate keyframes anywhere between 1 and 10 (don't touch 0). Be sure to close the action and reset bone transforms with Alt+R once you've finished.
* What is pairing? Pairing hands allows you to generate multiple macros in a single generate call. Actions will also be shared between all hands that are paired.

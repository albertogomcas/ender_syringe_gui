User friendly UI for a syringe pump built using ender 3 components following https://github.com/Vsaggiomo/Ender3-syringe-pumps

<img width="585" height="538" alt="syringe_gui" src="https://github.com/user-attachments/assets/610e0c82-9ae6-4eb4-a827-953bb42d980a" />

On this initial version only one pump is supported (Using the Z axis).
I used the 400 steps/mm of the included ender lead screw. The adapter pieces from Vsaggiomo must be modified to allow for about 8.5mm instead of a M5 screw (pretty simple since STEP files are included).
I am using an SKR mini V2 instead of the default ender control PCB.

You can edit and run the apply calibration function with the values needed for other steppers/screws/stepper drivers https://github.com/albertogomcas/ender_syringe_gui/blob/dbf53c2308f854dd06565f8b354fa32aebab25f9/syringe_gui.py#L12 It should should be fine to run this just once, the new values are stored into EEPROM.

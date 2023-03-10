@echo off
rem
rem RUN THIS BATCH FILE TO LAUNCH THE SKCC SKIMMER WEB APP ON WINDOWS
rem


rem check for config file placed in the same location as this batch file and 
rem copy them down to the directory where they are used. This only copys if the
rem files here are newer than the ones in skimmer_webapp\

if exist skimmerwebapp.cfg echo found skimmerwebapp.cfg && xcopy /F /y /q skimmerwebapp.cfg .\skimmer_webapp\
if exist skcc_skimmer.cfg echo found skcc_skimmer.cfg && xcopy /F /y /q skcc_skimmer.cfg .\skimmer_webapp\

cd .\skimmer_webapp\
start skimmer_webapp.exe
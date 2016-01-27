
set DIR=.

set HOST=dserver
set PORT=9572

;-------------------------------------------------------------------------------

echo "Grab test source, 'Sequence'"

%DIR%\dcl_test.exe  -h %HOST% -p %PORT% -s Sequence -n 3

echo "Grab test indexed source, 'Test'"

%DIR%\dcl_test.exe -h %HOST% -p %PORT% -s Test -i 4

echo "Grab test hashed source, 'Globals'"

%DIR%\dcl_test.exe -h %HOST% -p %PORT% -s Globals -I Password

pause

;-------------------------------------------------------------------------------


set confirm off
set pagination off
target remote localhost:{gdb_port}
# QEMU waits for gdb, program hasn't started yet
# Continue to let program run to completion
continue
# Program should complete quickly, now inspect memory at 0x40 (64)
# We expect the value 55 (0x37) = sum of 1 to 10
x/1xw 0x40
# Check registers
info registers r1
info registers r0
info registers r2
detach
quit


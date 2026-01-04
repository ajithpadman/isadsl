set confirm off
set pagination off
target remote localhost:{gdb_port}
# QEMU system mode with -S starts paused
# Set PC to entry point (0x10000 where binary is loaded)
set $pc = 0x10000
# Continue to let program run to completion
continue
# Program should complete quickly, now inspect memory
# In system mode, our program's address 64 (0x40) would be at 0x10040 (0x10000 + 0x40)
# We expect the value 55 (0x37) = sum of 1 to 10
x/1xw 0x10040
# Also check at the original address in case memory mapping is different
x/1xw 0x40
# Check registers
info registers r1
info registers r0
info registers r2
# Also try to read memory using register values
detach
quit


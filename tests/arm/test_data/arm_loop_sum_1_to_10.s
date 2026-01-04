# ARM assembly program to compute sum of 1 to 10
# Program: Sum of 1 to 10 (1+2+3+4+5+6+7+8+9+10 = 55) using labels and branches
# Since ARM subset only has unconditional B, we'll manually unroll the loop
# This tests that labels are correctly resolved and branches work
# We'll store the final result in memory so we can verify it
# Note: ARM immediate values are limited, so we'll use a smaller address

# Initialize: R0 = 0 (sum accumulator), R1 = 64 (memory address), R2 = 1 (counter)
# Note: ARM immediate values in MOV are limited (8 bits with rotation)
# So we'll use a smaller address that fits in 8 bits
MOV R0, #0          # sum = 0
MOV R1, #64         # memory address to store result (0x40 = 64, fits in 8 bits)
MOV R2, #1          # counter = 1

# Add counter to sum ten times using labels and branches
# R0 = R0 + R2, then increment R2, repeat until we've added 1 through 10
# Start with first addition
add1:
    ADD R0, R0, R2  # R0 = R0 + R2 = 0 + 1 = 1
    ADD R2, R2, #1  # R2 = R2 + 1 = 1 + 1 = 2
    B add2

add2:
    ADD R0, R0, R2  # R0 = R0 + R2 = 1 + 2 = 3
    ADD R2, R2, #1  # R2 = R2 + 1 = 2 + 1 = 3
    B add3

add3:
    ADD R0, R0, R2  # R0 = R0 + R2 = 3 + 3 = 6
    ADD R2, R2, #1  # R2 = R2 + 1 = 3 + 1 = 4
    B add4

add4:
    ADD R0, R0, R2  # R0 = R0 + R2 = 6 + 4 = 10
    ADD R2, R2, #1  # R2 = R2 + 1 = 4 + 1 = 5
    B add5

add5:
    ADD R0, R0, R2  # R0 = R0 + R2 = 10 + 5 = 15
    ADD R2, R2, #1  # R2 = R2 + 1 = 5 + 1 = 6
    B add6

add6:
    ADD R0, R0, R2  # R0 = R0 + R2 = 15 + 6 = 21
    ADD R2, R2, #1  # R2 = R2 + 1 = 6 + 1 = 7
    B add7

add7:
    ADD R0, R0, R2  # R0 = R0 + R2 = 21 + 7 = 28
    ADD R2, R2, #1  # R2 = R2 + 1 = 7 + 1 = 8
    B add8

add8:
    ADD R0, R0, R2  # R0 = R0 + R2 = 28 + 8 = 36
    ADD R2, R2, #1  # R2 = R2 + 1 = 8 + 1 = 9
    B add9

add9:
    ADD R0, R0, R2  # R0 = R0 + R2 = 36 + 9 = 45
    ADD R2, R2, #1  # R2 = R2 + 1 = 9 + 1 = 10
    B add10

add10:
    ADD R0, R0, R2  # R0 = R0 + R2 = 45 + 10 = 55
    # Store final result in memory before exiting
    STR R0, [R1, #0]  # Store R0 (should be 55) at address in R1 (64 = 0x40)
    B end_program   # Jump to end

# End program - exit syscall
end_program:
    MOV R7, #1      # syscall number for exit
    MOV R0, #0      # exit status (overwrite accumulator for clean exit)
    SVC #0          # make syscall


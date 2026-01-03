# ARM assembly program to test ISA DSL assembler
# This program performs basic arithmetic operations

# Load immediate values into registers
MOV R0, #10
MOV R1, #20

# Add R0 and R1, store result in R2
ADD R2, R0, R1

# Subtract R1 from R2, store result in R3
SUB R3, R2, R1

# Load another immediate
MOV R4, #5

# Add R3 and R4, store result in R5
ADD R5, R3, R4


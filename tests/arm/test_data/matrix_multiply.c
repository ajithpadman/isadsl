// Matrix multiplication test program
// Multiplies two 2x2 matrices: A * B = C
// A = [[1, 2], [3, 4]]
// B = [[5, 6], [7, 8]]
// Result: C = [[19, 22], [43, 50]]

int main() {
    // Matrix A: 2x2
    int A[2][2] = {{1, 2}, {3, 4}};
    // Matrix B: 2x2
    int B[2][2] = {{5, 6}, {7, 8}};
    // Result matrix C: 2x2
    int C[2][2] = {{0, 0}, {0, 0}};
    
    // Matrix multiplication: C[i][j] = sum of A[i][k] * B[k][j]
    int i, j, k;
    for (i = 0; i < 2; i++) {
        for (j = 0; j < 2; j++) {
            C[i][j] = 0;
            for (k = 0; k < 2; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
    
    // Return the sum of all elements in C as exit code
    // This allows us to verify the computation
    int sum = C[0][0] + C[0][1] + C[1][0] + C[1][1];
    return sum; // Should be 19 + 22 + 43 + 50 = 134
}


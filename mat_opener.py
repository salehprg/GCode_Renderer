import scipy.io

# Load the .mat file
mat_data = scipy.io.loadmat('CameraIntAruco_ExtAsym.mat')

# View the structure of the .mat file
print(mat_data.keys())

# Access a specific variable from the .mat file
# Replace 'variable_name' with the actual name of the variable you want to extract
your_variable = mat_data['variable_name']

# Print the extracted variable
print(your_variable)

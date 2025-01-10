import os 
import unittest
import multiprocessing
from client import validation_client
from server import validation_server 


# The simulated errors will be recorded in the log files, as if they occurred during normal operation.

class TestValidationClient(unittest.TestCase):

    def test_valid_inputs(self):
        """All the inputs provided are valid."""
        file = "file1.txt"
        operation = "BWT"
        host = "localhost"
        port = 12345
        try:
            # Create a temporary file
            with open(file, "w") as f:
                f.write("> header\n")  
                f.write("AGCTGCT")
            host, port, header, seq = validation_client(host, port, file, operation)
            self.assertEqual(host, "localhost")
            self.assertEqual(port, 12345)
            self.assertEqual(header, "> header")
            self.assertEqual(seq, "AGCTGCT")
        finally:
            # Remove the temporary file
            if os.path.exists(file):
                os.remove(file)

    
    def test_invalid_port(self):
        """Invalid port provided."""
        file = "file1.txt"
        operation = "BWT"
        host = "localhost"
        port = 123456789
        try:
            # Create a temporary file
            with open(file, "w") as f:
                f.write("> header\n")   
                f.write("AGCTGCT")
            # Check if the validation function raises a SystemExit due to invalid port
            with self.assertRaises(SystemExit) as cm:
                host, port, header, seq = validation_client(host, port, file, operation)
            # Verify that the exit code is 3
            self.assertEqual(cm.exception.code, 3)
        finally:
            # Remove the temporary file
            if os.path.exists(file):
                os.remove(file)


    def test_invalid_host(self):
        """Invalid host provided."""
        file = "file1.txt"
        operation = "BWT"
        host = "non_existent_host"
        port = 12345
        try:
            # Create a temporary file
            with open(file, "w") as f:
                f.write("> header\n")  
                f.write("AGCTGCT")
            # Check if the validation function raises a SystemExit due to invalid port
            with self.assertRaises(SystemExit) as cm:
                host, port, header, seq = validation_client(host, port, file, operation)
            # Verify that the exit code is 4
            self.assertEqual(cm.exception.code, 4)
        finally:
            # Remove the temporary file
            if os.path.exists(file):
                os.remove(file)


    def test_invalid_file(self):
        """File provided not found."""
        file = "file1.txt"
        operation = "BWT"
        host = "localhost"
        port = 12345
        
        # Check if the validation function raises a SystemExit due to non existent file
        with self.assertRaises(SystemExit) as cm:
            host, port, header, seq = validation_client(host, port, file, operation)
        # Verify that the exit code is 2
        self.assertEqual(cm.exception.code, 2)
        

    def test_invalid_file_extension(self):
        """Invalid file provided (extension)."""
        file = "file1.docx"
        operation = "BWT"
        host = "localhost"
        port = 12345
        try:
            # Create a temporary file
            with open(file, "w") as f:
                f.write("> header\n")  
                f.write("AGCTGCT")
            # Check if the validation function raises a SystemExit due to invalid port
            with self.assertRaises(SystemExit) as cm:
                host, port, header, seq = validation_client(host, port, file, operation)
            # Verify that the exit code is 3
            self.assertEqual(cm.exception.code, 3)
        finally:
            # Remove the temporary file
            if os.path.exists(file):
                os.remove(file)

    
    def test_invalid_operation(self):
        """REVERT operation with a BWT string that does not contain the $ terminator character."""
        file = "file1.txt"
        operation = "REVERT"
        host = "localhost"
        port = 12345
        try:
            # Create a temporary file
            with open(file, "w") as f:
                f.write("> header\n")  
                f.write("AGCTGCT")
            # Check if the validation function raises a SystemExit due to invalid port
            with self.assertRaises(SystemExit) as cm:
                host, port, header, seq = validation_client(host, port, file, operation)
            # Verify that the exit code is 3
            self.assertEqual(cm.exception.code, 3)
        finally:
            # Remove the temporary file
            if os.path.exists(file):
                os.remove(file)

    
    def test_invalid_header(self):
        """Invalid header."""
        file = "file1.txt"
        operation = "BWT"
        host = "localhost"
        port = 12345
        try:
            # Create a temporary file
            with open(file, "w") as f:
                f.write("header\n")      # missing ">""
                f.write("AGCTGCT")
            # Check if the validation function raises a SystemExit due to invalid port
            with self.assertRaises(SystemExit) as cm:
                host, port, header, seq = validation_client(host, port, file, operation)
            # Verify that the exit code is 3
            self.assertEqual(cm.exception.code, 3)
        finally:
            # Remove the temporary file
            if os.path.exists(file):
                os.remove(file)

    
    def test_invalid_sequence(self):
        """The sequence contains an invalid base ("F")."""
        file = "file1.txt"
        operation = "BWT"
        host = "localhost"
        port = 12345
        try:
            # Create a temporary file
            with open(file, "w") as f:
                f.write("> header\n")  
                f.write("AGCTGCTF")
            # Check if the validation function raises a SystemExit due to invalid port
            with self.assertRaises(SystemExit) as cm:
                host, port, header, seq = validation_client(host, port, file, operation)
            # Verify that the exit code is 3
            self.assertEqual(cm.exception.code, 3)
        finally:
            # Remove the temporary file
            if os.path.exists(file):
                os.remove(file)



# To validate the Host and Port, the validation_server function uses the same logic used by the validation_client function. For this reason, 
# no examples with invalid Host or Port are provided below.

class TestValidationServer(unittest.TestCase):

    def test_valid_inputs(self):
        """All the inputs provided are valid."""
        host = "localhost"
        port = 12345
        n_processes = multiprocessing.cpu_count() - 1  # Assuming this is the result of the CPU cores count
        
        host, port, n_processes = validation_server(host, port, n_processes)
        
        self.assertEqual(host, "localhost")
        self.assertEqual(port, 12345)
        self.assertEqual(n_processes, multiprocessing.cpu_count() - 1)


    def test_invalid_n_processes(self):
        """Invalid number of processes provided: more than the number of CPU cores."""
        host = "localhost"
        port = 12345
        n_processes = multiprocessing.cpu_count() * 2 + 5 

        with self.assertRaises(SystemExit) as cm:
            # Check if the validation function raises a SystemExit due to invalid number of processes
            host, port, n_processes = validation_server(host, port, n_processes)
        # Verify that the exit code is 3
        self.assertEqual(cm.exception.code, 3)



if __name__ == "__main__":
    unittest.main()


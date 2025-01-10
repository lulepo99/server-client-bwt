import sys
import os
import socket
import argparse
import logging
from datetime import datetime


# Configure logging to record client activity
logging.basicConfig(filename="client_activity.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filemode="a")

def validation_client(host, port, file, operation):
    """
    The function checks for the validation of the inputs provided. If errors are generated, they are handled through logging messages and exit codes.
    Otherwise, the function returns the parameters.
    """
    try:
        # Port and Host validation
        if not (1 <= port <= 65535):
            raise ValueError(f"Invalid port: {port}. Port number must be between 1 and 65535.")
        socket.gethostbyname(host)
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        sys.exit(3)
    except socket.gaierror:
        logging.error(f"Invalid host: {host}. Host could not be resolved.")
        sys.exit(4)
    
    try:
        # Check the validity of the input file
        if not (file.endswith(".txt") or file.endswith(".fasta")):
            raise ValueError("Invalid input file. The input file must have a .txt or .fasta extension.")

        # Read the DNA sequence from the input file and store it in the "seq" variable 
        with open(file, "r") as f:
            header = f.readline().strip()       # Read the header
            seq = f.read().strip().upper()      # Read the sequence removing extra whitespace and convert to upper case
            seq = seq.replace("\n", "")         # Remove newline characters in the sequence (normally present in fasta files)
            # Validation of the input file
            if not header.startswith(">"):  
                raise ValueError("Invalid file format: The header must start with '>'.")
            if not seq:
                raise ValueError("The input file is empty.")
            if operation == "BWT" and seq.count('$') > 0:
                raise ValueError("Invalid operation: '$' terminator must not be present for BWT.")
            if operation == "REVERT" and seq.count('$') != 1:
                raise ValueError("Invalid operation: '$' terminator must be present exactly once for REVERT.")
            if not all(base in "ACGTRYSWKMBDHVN$" for base in seq):      # IUPAC nucleotide code
                raise ValueError("The sequence contains invalid bases.")
        logging.info(f"File {file} successfully opened. Sequence lenght: {len(seq)}.")
    except FileNotFoundError:
        logging.error(f"Error: file {file} not found.")
        sys.exit(2)
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        sys.exit(3)
    return host, port, header, seq


def main():

    # Add an empty line in the log file to separate the previous process
    with open("client_activity.log", "a") as f:
        f.write("\n")

    logging.info("Starting a new request...")

    parser = argparse.ArgumentParser(description = "Implementation of a server along with a corresponding client to process DNA sequences.\n"
                                     "Supported operations:\n- BWT: Burrows-Wheeler Transform.\n- REVERT: Reverse the transformation.",
                                     formatter_class = argparse.RawTextHelpFormatter)

    # Parse command-line arguments for host and port
    parser.add_argument("-H", "--host", default = "localhost", help = "Host address for the server. Default: localhost.")
    parser.add_argument("-p", "--port", type = int, default = 12345, help = "Port for the server. Default: 12345.")
    
    # Parse command-line arguments for operation type (BWT or REVERT) and input file with the sequence
    parser.add_argument("-o", "--operation", required = True, choices=["BWT", "bwt", "REVERT", "revert"], help = "Operation to execute: BWT or REVERT.")
    parser.add_argument("-f", "--file", required = True, help = "Path to the file containing the DNA sequence.\n" 
                                                                "The input file must be a .txt or .fasta file and must contain exactly one header line," 
                                                                "starting with `>`, followed by a single sequence.", metavar = "INPUT FILE")
    
    args = parser.parse_args()

    args.operation = args.operation.upper() # convert to uppercase

    # Input validation. If successful, the parameter seq representing the sequence is returned. Otherwise, an error is generated and the program ends
    host, port, header, seq = validation_client(args.host, args.port, args.file, args.operation)

    try:
        # Create a socket for the client and connect to the server
        s = socket.socket()
        s.settimeout(300)      # a large limit to ensure that also a large sequence can be sent to the server
        s.connect((host, port))
        logging.info(f"Connecting to server at {host}: {port}.")

        # Receive the welcome message from the server
        welcome = s.recv(1024).decode()
        logging.info(welcome)

        # Send the operation and sequence to the server with the end delimiter
        data = f"{args.operation}: {seq}\n"
        s.sendall(data.encode())
        logging.info("All data successfully sent to the server.")

        raw_seq = b""      # Variable to store the received data
        end = b"\n"      # Delimiter indicating the end of data transmission

        # Receive the converted sequence from the server
        while True:
            data = s.recv(1024)
            if end in data:
                raw_seq += data[:data.find(end)]
                logging.info("All data successfully received from the server.")
                break
            raw_seq += data
        
        seq = raw_seq.decode()      # Decode the received data
   
    except socket.timeout:
        logging.error("SOCKET TIMEOUT ERROR: Connection timed out during data transmission.")
        sys.exit(5)
    except BrokenPipeError:
        logging.error("BROKEN PIPE ERROR: Tried to send data to a closed connection.")
        sys.exit(6)
    except ConnectionRefusedError:
        logging.error("CONNECTION REFUSED ERROR: Connection refused by the server.")
        sys.exit(7)
    except ConnectionResetError:
        logging.error("CONNECTION RESET ERROR: Connection forcibly closed during data transmission.")
        sys.exit(8)
    except socket.error as e:
        logging.error(f"SOCKET ERROR: {e}.")
        sys.exit(9)
    except Exception as e:
        logging.error(f"UNEXPECTED ERROR: {e}.")
        sys.exit(1)

    finally:
        # Close the connection with the server
        s.close()
        logging.info(f"Connection to server {host}: {port} closed.")

    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        file_name = os.path.splitext(args.file)[0]

        # Generate the output file name
        output_file = f"{file_name}_{args.operation.lower()}_{timestamp}_output.txt"
        
        # Write the operation performed and the converted sequence to an output file
        with open(output_file, "w") as f:
            f.write(f"{header}\nOperation performed: {args.operation}\n\nOutput sequence: {seq}")
        logging.info(f"File {output_file} created and compiled.")

    except OSError as e:
        logging.error(f"Error during file writing: {e}.")
        sys.exit(10)


# Start the client only if the script is executed directly from the command line
if __name__ == "__main__":
    main()



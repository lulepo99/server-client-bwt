import sys
import socket
import argparse
import logging
import multiprocessing
from conversion_functions import burrows_wheeler_conversion, revert_burrows_wheeler


# Configure logging to record server activity
logging.basicConfig(filename="server_activity.log", level=logging.INFO, format="%(asctime)s - PID %(process)d - %(levelname)s - %(message)s", filemode="a")

def handle_request(conn, addr):
    """
    Function to handle client requests
    """

    logging.info("Starting a new process...") 
    raw_seq_info = b""      # Variable to store the received data
    end = b"\n"      # Delimiter indicating the end of data transmission
    
    try:
        # Receive the data from the client until the end delimiter is found
        while True:
            data = conn.recv(1024)
            if end in data:
                raw_seq_info += data[:data.find(end)]
                logging.info("All data successfully received from the server.")
                break
            raw_seq_info += data

        # Decode the received data and store the operation to perform and the sequence to convert
        seq_info = raw_seq_info.decode()
        operation, seq_to_convert = seq_info.split(": ")

        # Execute the requested operation (BWT or REVERT)
        if operation == "BWT":
            result = burrows_wheeler_conversion(seq_to_convert)
            logging.info(f"BWT operation completed for {addr}")
        else:
            result = revert_burrows_wheeler(seq_to_convert)
            logging.info(f"REVERT operation completed for {addr}")

        # Send the result back to the client
        conn.sendall((result + "\n").encode())
        logging.info(f"All data successfully sent to {addr}.")         

    except socket.timeout:
        logging.error("SOCKET TIMEOUT ERROR: Connection timed out during data transmission.")
    except ConnectionResetError:
        logging.error("CONNECTION RESET ERROR: Connection forcibly closed during data transmission.")
    except socket.error as e:
        logging.error(f"SOCKET ERROR: {e}.")
    except Exception as e:
        logging.error(f"UNEXPECTED ERROR: {e}.")
    finally:
        # Close the connection with the client
        conn.close()
        logging.info(f"Process completed. Closed connection with client {addr}.")


def validation_server(host, port, n_processes):
        """
        The function checks for the validation of the inputs provided. If errors are generated, they are handled through logging messages and exit codes. 
        Otherwise, the function returns the parameters.
        """
        try:
            # Port and Host validation
            if not (1 <= port <= 65535):
                raise ValueError(f"Invalid port: {port}. Port number must be between 1 and 65535.")
            socket.gethostbyname(host)

            # The number of processes to manage simultaneously with multiprocessing.Pool depends on the number of CPU cores available. 
            # Default is the number of CPU cores - 1 since the tasks performed by the server are mainly CPU-bound.
            # Advanced users can specify a different number via command line. If this number is less than 1 or more than twice the number
            # of CPU cores, a ValueError is raised.
            if n_processes < 1 or n_processes > multiprocessing.cpu_count() * 2:
                raise ValueError(f"Invalid number of processes: {n_processes}. It must be between 1 and {multiprocessing.cpu_count() * 2}"
                                 f"Default is {multiprocessing.cpu_count() -1}")  
        except ValueError as e:
            logging.error(f"Validation error: {e}")
            sys.exit(3)
        except socket.gaierror:
            logging.error(f"Invalid host: {host}. Host could not be resolved.")
            sys.exit(4)
        return host, port, n_processes


def starting():
    """
    Funtion to start the server and manage client connections. The server listens on a host and 
    a port specificied in the server_config file.
    """
    logging.info("Server is starting...")

    parser = argparse.ArgumentParser(description = "Implementation of a server along with a corresponding client to process DNA sequences.\n"
                                     "Supported operations:\n  - BWT: Burrows-Wheeler Transform.\n  - REVERT: Reverse the transformation.",
                                     formatter_class = argparse.RawTextHelpFormatter)

    # Parse command-line arguments for host, port, and number of processes to run simultaneously
    parser.add_argument("-H", "--host", default = "localhost", help = "Host address for the server. Default: localhost.")
    parser.add_argument("-p", "--port", type = int, default = 12345, help = "Port for the server. Default: 12345.")
    parser.add_argument("--processes", type = int, default = max(1, multiprocessing.cpu_count() - 1), help = "Number of processes to run simulatneously.\n"
                        "Default: number of CPU cores - 1 (at least 1).\nIt is highly recommended to leave the default unless you have a specific reason to change it.\n"
                        "Advanced users can specify a number between 1 and twice the number of CPU cores (included).")
    
    args = parser.parse_args()

    # Validation of the inputs provided using the validation_server function
    host, port, n_processes = validation_server(args.host, args.port, args.processes)

    logging.info(f"Validation successful. Server can manage {n_processes} processes simultaneously")

    # Create a socket for the server
    s = socket.socket()

    try:
        # Bind the address (host + port) to the socket and start listening
        s.bind((host, port))
        s.listen(5)
        logging.info(f"Server started at {host}: {port}. Waiting for connections...")

        # Add an empty line in the log file to separate the server starting from the connections
        with open("server_activity.log", "a") as f:
            f.write("\n")

        # Use multiprocessing.Pool to handle simultaneous connections from different clients. 
        with multiprocessing.Pool(processes=n_processes) as pool:
            while True:
                conn, addr = s.accept()      # Accept the client connection
                logging.info(f"Got connection from {addr}")
                conn.send(b"Welcome. Waiting for data...")      # Send a welcome message to the client
                conn.settimeout(300)      # a large limit to ensure that also a large sequence can be sent back to the client

                pool.apply_async(handle_request, args=(conn, addr))      # Process in a separate process

    except socket.error as e:
        logging.error(f"SOCKET ERROR: {e}.")
        sys.exit(9)
    except Exception as e:
        logging.error(f"UNEXPECTED ERROR: {e}.")
        sys.exit(1)

        
# Start the server only if the script is executed directly from the command line
if __name__ == "__main__":
    starting()



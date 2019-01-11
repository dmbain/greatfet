#
# This file is part of GreatFET
#

from ..protocol import vendor_requests
from ..peripheral import GreatFETPeripheral

class I2CBus(GreatFETPeripheral):
    """
        Class representing a GreatFET I2C bus.

        For now, supports only the primary I2C bus (I2C0), but will be
        expanded when the vendor commands are.
    """

    # Master Transmitter/Receiver mode should return 0x18/0x40 respectively
    VALID_STATES = [0x18, 0x40]

    def __init__(self, board, name='i2c bus', buffer_size=255, duty_cycle_count=255):
        """
            Initialize a new I2C bus.

            Args:
                board -- The GreatFET board whose I2C bus we want to control.
                name -- The display name for the given I2C bus.
                buffer_size -- The size of the I2C receive buffer on the GreatFET.
        """

        # Store a reference to the parent board.
        self.board = board

        # Store our limitations.
        self.buffer_size = buffer_size

        # Create a list that will store all connected devices.
        self.devices = []

        # Store our duty cycle count
        self.duty_cycle_count = duty_cycle_count

        # Set up the I2C bus for communications.
        board.apis.i2c.start(duty_cycle_count)

    def attach_device(self, device):
        """
            Attaches a given I2C device to this bus. Typically called
            by the I2C device as it is constructed.

            Arguments:
                device -- The device object to attach to the given bus.
        """

        # TODO: Check for address conflicts!

        self.devices.append(device)


    def transmit(self, address, data, receive_length=0):
        """
            Sends data over the I2C bus, and optionally recieves
            data in response.

            Args:
                address -- The I2C address for the target device.
                    Should not contain read/write bits. Can be used to address
                    special addresses, for now; but this behavior may change.
                data -- The data to be sent to the given device.
                receive_length -- If provided, the I2C controller will attempt
                        to read the provided amount of data, in bytes.
        """

        if (not isinstance(receive_length, int)) or receive_length < 0:
            raise ValueError("invalid receive length!")

        if receive_length > self.buffer_size:
            raise ValueError("Tried to receive more than the size of the receive buffer.");

        if address > 127 or address < 0:
            raise ValueError("Tried to transmit to an invalid I2C address!")

        # Perform the core transfer, parse status and device response
        data = bytes(data)
        usb_response = self.board.apis.i2c.xfer(address, receive_length, data)
        device_response = usb_response[:-1]
        status = usb_response[-1]

        return device_response, status


    def scan(self):
        """
            Sends empty data over the I2C bus, and recieves ACK/NAK
            in response for valid/invalid addresses.
        """
        
        valid_addresses = []
        for address in range(0, 256, 2):
            # Perform the core transfer, parse status and device response
            usb_response = self.board.apis.i2c.xfer(address >> 1, 1, b'')
            status = usb_response[-1]
            device_response = usb_response[:-1]

            if status in I2CBus.VALID_STATES:
                valid_addresses.append(address)

        return valid_addresses


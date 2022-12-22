#include <msp430.h> 


#define bufferSize 150              // Buffer size for UART receiving

// UART Variables
unsigned volatile int circBuffer[bufferSize];                   // For storing received data packets
unsigned volatile int head = 0;                                 // circBuffer head
unsigned volatile int tail = 0;                                 // circBuffer tail
unsigned volatile int length = 0;                               // circBuffer length
unsigned volatile int rxByte = 0;                               // Temporary variable for storing each received byte
volatile int rxFlag = 0;                                        // Received data flag, triggered when a packet is received
volatile int rxIndex = 0;                                       // Counts bytes in data packet

// Control Variables and constants
unsigned volatile int xSpeed = 2000;
unsigned volatile int ySpeed = 2000;
unsigned volatile int xLoc = 0;
unsigned volatile int yLoc = 0;
unsigned volatile int xr = 0;
unsigned volatile int yr = 0;
volatile int xError = 0;
volatile int yError = 0;
unsigned volatile int magnetState = 0;
unsigned volatile int movingState = 0;
unsigned volatile int calibrationState = 0;

// Function to transmit a UART package given arguments for package
void transmitPackage(unsigned int instrByte, unsigned int dataByte1, unsigned int dataByte2, unsigned int dataByte3, unsigned int dataByte4){
    unsigned int decoderByte = 0;
    if (dataByte1 == 255){
        decoderByte |= 8;
        dataByte1 = 0;
    }
    if (dataByte2 == 255){
        decoderByte |= 4;
        dataByte2 = 0;
    }
    if (dataByte3 == 255){
        decoderByte |= 2;
        dataByte3 = 0;
    }
    if (dataByte4 == 255){
        decoderByte |= 1;
        dataByte4 = 1;
    }
    while (!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = 255;
    while (!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = instrByte;
    while (!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = dataByte1;
    while (!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = dataByte2;
    while (!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = dataByte3;
    while (!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = dataByte4;
    while (!(UCA1IFG & UCTXIFG));
    UCA1TXBUF = decoderByte;
    while (!(UCA1IFG & UCTXIFG));
}

// Main Loop for initialization, reading of UART buffer, and starting commands
int main(void)
{
    WDTCTL = WDTPW | WDTHOLD;   // stop watchdog timer

    // Configure Clocks
    CSCTL0 = 0xA500;                            // Write password to modify CS registers
    CSCTL1 = DCORSEL;                           // DCO = 16 MHz
    CSCTL2 |= SELM_3 + SELS_3 + SELA_3;         // MCLK = DCO, ACLK = DCO, SMCLK = DCO
    CSCTL3 |= DIVS_5;                           // Set divider for SMCLK (/32) -> SMCLK 500kHz

    // Configure pins for Magnet
    P1DIR |= BIT4;
    P1OUT &= ~(BIT4);

    // Configure timer B1 for X Stepper Motor
    TB1CTL |= TBSSEL_1 + TBIE + MC_1 + TBCLR;
    TB1CCTL1 |= OUTMOD_3;
    TB1CCR0 = 0;
    TB1CCR1 = xSpeed/2;

    // Configure Pin for B1 timer (X Stepper Motor)
    P1DIR |= BIT6;
    P1SEL0 |= BIT6;
    P1SEL1 &= ~BIT6;

    // Configure Pin for X Stepper Direction
    P1DIR |= BIT3;

    // Configure timer B2 for Y Stepper Motor
    TB2CTL |= TBSSEL_1 + MC_1 + TBIE + TBCLR;
    TB2CCTL1 |= OUTMOD_3;
    TB2CCR0 = 0;
    TB2CCR1 = ySpeed/2;

    // Configure Pin for B2 timer (Y Stepper Motor)
    P2DIR |= BIT1;
    P2SEL0 |= BIT1;
    P2SEL1 &= ~BIT1;

    // Configure Pin for Y Stepper Direction
    P3DIR |= BIT3;

    // Initialize Limit Switches
    P3DIR &= ~(BIT5 + BIT6); // X Axis and Y Axis Respectively
    P3REN |= BIT5 + BIT6; // Input w/ Pullup or down set
    P3OUT &= ~(BIT5 + BIT6); // Pull Down Resistor set

    // Initialize Limit Switch Interrupts
    P3IES |= BIT5 + BIT6; // Set on High to Low Transition
    P3IE |= BIT5 + BIT6;

    // Configure ports for UART
    P2SEL0 &= ~(BIT5 + BIT6);
    P2SEL1 |= BIT5 + BIT6;

    // Configure UART
    UCA1CTLW0 |= UCSSEL0;
    UCA1MCTLW = UCOS16 + UCBRF0 + 0x4900;   // Define UART as 19200baud rate
    UCA1BRW = 52;
    UCA1CTLW0 &= ~UCSWRST;
    UCA1IE |= UCRXIE;                       //enable UART receive interrupt
    _EINT();                                //Global interrupt enable

    // Circular Buffer Data Processing Variables
    unsigned volatile int commandByte, dataByte1, dataByte2, dataByte3, dataByte4, escapeByte, firstDataByte, secondDataByte;

    while (1)
    {
        if (rxFlag)
        {
            // Get escape byte and command byte from buffer
            escapeByte = circBuffer[head - 1];
            commandByte = circBuffer[head - 6];

            // Handle the Data Bytes
            // Check if the first bit of escape byte is 1 and if so set dataByte4 to 255
            if (escapeByte & 1) { dataByte4 = 255; }
            // Else, dataByte4 gets the value from the buffer
            else { dataByte4 = circBuffer[head - 2]; }
            // Check if the second bit of escape byte is 1 and if so set dataByte3 to 255
            if (escapeByte & 2) { dataByte3 = 255; }
            // Else, dataByte3 gets the value from the buffer
            else { dataByte3 = circBuffer[head - 3]; }
            // Check if the third bit of escape byte is 1 and if so set dataByte2 to 255
            if (escapeByte & 4) { dataByte2 = 255; }
            // Else, dataByte2 gets the value from the buffer
            else { dataByte2 = circBuffer[head - 4]; }
            // Check if the fourth bit of escape byte is 1 and if so set dataByte1 to 255
            if (escapeByte & 8) { dataByte1 = 255; }
            // Else, dataByte1 gets the value from the buffer
            else { dataByte1 = circBuffer[head - 5]; }

            // DataByte gets the combination of dataByte1 & dataByte2
            firstDataByte = (dataByte1 << 8) + dataByte2;
            secondDataByte = (dataByte3 << 8) + dataByte4;


            // Handle the command Bytes
            switch(commandByte)
            {
            case 0: // Move with Magnet Off
                // Turn off magnet P1.4
                P1OUT &= ~BIT4;
                magnetState = 0;
                // Set new XY goal position
                xr = firstDataByte;
                yr = secondDataByte;
                movingState = 1;
                // Check initial x and y error to only start motors that are necessary
                xError = xr-xLoc;
                yError = yr-yLoc;
                if (xError != 0){
                    TB1CCR0 = xSpeed;
                }
                if (yError != 0){
                    TB2CCR0 = ySpeed;
                }
                break;
            case 1: // Move with Magnet On
                // Turn on magnet P1.4
                P1OUT |= BIT4;
                magnetState = 1;
                // Set new XY goal position
                xr = firstDataByte;
                yr = secondDataByte;
                movingState = 1;
                // Check initial x and y error to only start motors that are necessary
                xError = xr-xLoc;
                yError = yr-yLoc;
                if (xError != 0){
                    TB1CCR0 = xSpeed;
                }
                if (yError != 0){
                    TB2CCR0 = ySpeed;
                }
                break;
            case 2: // Zero Steppers Not fully implemented but not fully necessary
                calibrationState = 1;
                while(calibrationState == 1){
                    P3OUT |= BIT3;
                    P1OUT |= BIT3;
                    TB1CCR0 = xSpeed;
                }
                xr = 1000; // Might not need these parts if only triggers on falling edge
                movingState = 1;
                TB1CCR0 = xSpeed;
                calibrationState = 1;
                while(calibrationState == 1){
                    P3OUT &= ~BIT3;
                    P1OUT &= ~BIT3;
                    TB2CCR0 = xSpeed;
                }
                yr = 1000;
                movingState = 1;
                TB1CCR0 = xSpeed;
                transmitPackage(2, xLoc>>8,xLoc&0xFF,yLoc>>8,yLoc&0xFF);
                break;
            default: // No known command
                break;
            }

            // Remove the processed bytes from the buffer
            length -= 7;                                // Decrease length by 7
            if (bufferSize - tail <= 7) { tail = 0; }   // Check if tail at end of buffer and if so put it at start
            else { tail += 7; }                         // Else, increase tail by 7

            // reset the data received flag
            rxFlag = 0;
        }

        // If both motors have arrived turn off both motors
        if (movingState == 1 && xError == 0 && yError == 0){
            movingState = 0;
            TB2CCR0 = 0;
            TB1CCR0 = 0;
            transmitPackage(magnetState, xLoc>>8, xLoc&0xFF, yLoc>>8, yLoc&0xFF);
        }
    }
    return 0;
}

// UART interrupt to fill receive buffer with data sent from C# program
#pragma vector = USCI_A1_VECTOR
__interrupt void USCI_A1_ISR(void)
{
    rxByte = UCA1RXBUF;                 // rxByte gets the received byte

    // Check if 255 was received
    if (rxByte == 255 || rxIndex > 0)
    {
        // Check that the buffer isn't full
        if (length < bufferSize)
        {
            circBuffer[head] = rxByte;      // Buffer gets received byte at head
            length++;                       // Increment length

            if (head == bufferSize) { head = 0; }   // Check if head at end of buffer and if so put it at start
            else { head++; }                // Else, increment head

            // Check if receiving index is 6 or greater and if so reset
            if (rxIndex >= 6)
            {
                rxIndex = 0;                // Reset receiving index
                rxFlag = 1;                 // Set the data received flag
            }
            else { rxIndex++; }             // Increment rxIndex
        }
    }
}

// Timer B1 Overflow Interrupt: Increment X Stepper
// Triggers on each timer/step pulse
#pragma vector = TIMER1_B1_VECTOR
__interrupt void IncrementXStepper(void){
    // If flag for moving is set
    if (movingState){
        // Calculate error, set direction, and inc or dec Location counter
        xError = xr - xLoc;
            if (xError == 0){
                TB1CCR0 = 0;
            }
            else if (xError > 0){
                xLoc++;
                P1OUT |= BIT3;
            }
            else if (xError < 0){
                xLoc--;
                P1OUT &= ~BIT3;
            }
    }
    TB1CTL &= ~TBIFG;
}

// Timer B2 Overflow Interrupt: Increment Y Stepper
// Triggers on each timer/step pulse
#pragma vector = TIMER2_B1_VECTOR
__interrupt void IncrementYStepper(void){
    // If flag for moving is set
    if (movingState){
        // Calculate error, set direction, and inc or dec Location counter
        yError = yr - yLoc;
           if (yError == 0){
               TB2CCR0 = 0;
           }
           else if (yError > 0){
               yLoc++;
               P3OUT |= BIT3;
           }
           else if (yError < 0){
               yLoc--;
               P3OUT &= ~BIT3;
           }
    }
    TB2CTL &= ~TBIFG;
}

// Limit Switch Interrupt
// Not fully implemented as limit switches didn't fit in mechanical design
#pragma vector = PORT3_VECTOR
__interrupt void SwitchToggle (void){
    // If limit switch GPIO is brought low stop both motors, and set corresponding motor to location values
    TB1CCR0 = 0;
    TB2CCR0 = 0;
    calibrationState = 0;
    if (P3IV & BIT5){
        xLoc = 0; // X Location of Limit Switch
        P3IFG &= ~BIT5;
    }
    if (P3IV & BIT6){
        yLoc = 4000; // Y location of limit switch
        P3IFG &= ~BIT6;
    }
}

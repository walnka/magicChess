#include <msp430.h> 


#define bufferSize 150              // Buffer size for UART receiving
//#define numPhases 8                 // Defined for easier switching between full and half steps during debugging
//#define xControlRefresh 0x1388      // Delay for x Control Loop during control operation (20ms)
//#define xRegularRefresh 0xC350      // Delay for x Control Loop during non-control operation (200ms)
// Note: For smoother slider DC control change xRegularRefresh to 0x1388 (control tuning is off when this happens though)

// UART Variables
unsigned volatile int circBuffer[bufferSize];                   // For storing received data packets
unsigned volatile int head = 0;                                 // circBuffer head
unsigned volatile int tail = 0;                                 // circBuffer tail
unsigned volatile int length = 0;                               // circBuffer length
unsigned volatile char* bufferFullMsg = "Buffer is full";       // Message to print when buffer is full
unsigned volatile char* bufferEmptyMsg = "Buffer is empty";     // Message to print when buffer is empty
unsigned volatile int rxByte = 0;                               // Temporary variable for storing each received byte
volatile int rxFlag = 0;                                        // Received data flag, triggered when a packet is received
volatile int rxIndex = 0;                                       // Counts bytes in data packet



//volatile int contStepperMode = 0;                               // 0 = No power to motor, 1 = CW dir continuous, -1 = CCW dir continuous, 2 = single step mode
//
//// Variables for Y Control (Stepper)
//unsigned volatile int yr = 0;                                   // Goal loc for Y controller
//unsigned volatile int yControlFlag = 0;                         // Signals whether Y is in a control loop
//unsigned int yLoc = 0;                                          // Current location of Y

unsigned volatile int xSpeed = 2000;
unsigned volatile int ySpeed = 2000;
unsigned volatile int xLoc = 0;
unsigned volatile int yLoc = 0;
unsigned volatile int xr = 0;
unsigned volatile int yr = 0;
volatile int xError = 0;
volatile int yError = 0;
unsigned volatile int magnetPower = 0x3E8;

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

    // Configure timer B0 for Magnet PWM
    TB0CTL |= TBSSEL_1 + MC_1 + ID_1 + TBCLR;           // ACLK, up mode (16MHz/2 = 8MHz)
    TB0CCTL0 |= CCIE;                               // CCR0 interrupt enable
    TB0CCTL1 |= CCIE;
    TB0CCR0 = magnetPower; //timerVal;                         // CCR0: interrupt for half step phase switching
    TB0CCR1 = 0x300;
    // Configure pins for Magnet PWM
    P1DIR |= BIT4 + BIT5;
    P1OUT &= ~(BIT4 + BIT5);

    // Configure timer B1 for X Stepper Motor
    TB1CTL |= TBSSEL_1 + TBIE + MC_1 + TBCLR; // start with timer off
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
                transmitPackage(1, firstDataByte>>8,firstDataByte&0xFF,secondDataByte>>8,secondDataByte&0xFF);
                P1OUT ^= BIT3;
                TB0CCR0 = 0;
                xr = firstDataByte;
                yr = firstDataByte;
                if (xr-xLoc != 0){
                    TB1CCR0 = xSpeed;
                }
                if (yr-yLoc != 0){
                    TB2CCR0 = ySpeed;
                }
                break;
            case 1: // Move with Magnet On
                transmitPackage(3, firstDataByte>>8,firstDataByte&0xFF,secondDataByte>>8,secondDataByte&0xFF);
                TB0CCR0 = magnetPower;
                xr = firstDataByte;
                yr = firstDataByte;
                if (xr-xLoc != 0){
                    TB1CCR0 = xSpeed;
                }
                if (yr-yLoc != 0){
                    TB2CCR0 =ySpeed;
                }
                break;
            case 2: // Zero Steppers
                xLoc = 0;
                yLoc = 0;
                transmitPackage(2, xLoc>>8,xLoc&0xFF,yLoc>>8,yLoc&0xFF);
                break;
            default: // No known command
                break;
            }

//          Remove the processed bytes from the buffer
            length -= 7;                        // Decrease length by 5
            if (bufferSize - tail <= 7) { tail = 0; }   // Check if tail at end of buffer and if so put it at start
            else { tail += 7; }                 // Else, increase tail by 5

            // reset the data received flag
            rxFlag = 0;
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
#pragma vector = TIMER1_B1_VECTOR
__interrupt void IncrementXStepper(void){
    xError = xr - xLoc;
    if (xError == 0){
        TB1CCR0 = 0;
    }
    else if (xError > 0){
        xLoc++;
        // Set Direction to Positive
    }
    else if (xError < 0){
        xLoc--;
        // Set Direction to Negative
    }
    transmitPackage(0, xLoc>>8, xLoc&0xFF, 0, 0);
    TB1CTL &= ~TBIFG;
}

// Timer B2 Overflow Interrupt: Increment Y Stepper
#pragma vector = TIMER2_B1_VECTOR
__interrupt void IncrementYStepper(void){
    yError = yr - yLoc;
    if (yError == 0){
        TB2CCR0 = 0;
    }
    else if (yError > 0){
        yLoc++;
        // Set Direction to Positive
    }
    else if (yError < 0){
        yLoc--;
        // Set Direction to Negative
    }
    transmitPackage(1, yLoc>>8, yLoc&0xFF, yr>>8, yr&0xFF);
    TB2CTL &= ~TBIFG;
}

// Timer B1 CCR1 Interrupt: Turn off stepper phases for PWM
#pragma vector = TIMER0_B1_VECTOR
__interrupt void TurnOffStepperPhases(void){
    P1OUT |= BIT4;
    TB0CCTL1 &= ~CCIFG;
}

// Timer B1 CCR0 Interrupt: Turn on proper stepper phases for PWM
#pragma vector = TIMER0_B0_VECTOR
__interrupt void TurnOnStepperPhases(void){
    P1OUT &= ~BIT4;
    TB0CCTL0 &= ~CCIFG;
}

#include <msp430.h> 

// Control Constants
#define Kangle 197/180
#define zeroAngleOffset 504
#define Ktimer 800
#define Kp 2000.0//2222.0
#define Kw 4000.0 //10000.0
#define Kmult 8000000/Kp
#define averageWindow 10
#define timeDelay 5 // ms

volatile int x = 0;
volatile int angle = 0;
volatile double timerVal = 0xFFFF;
volatile double angVelo[averageWindow];
volatile double avgAngVelo = 0.0;

//double averageAngVelo(int newAngle)
//{
//    double average = 0.0;
//    int count = 1;
//    for (count; count<averageWindow; count++){
//        average += (angVelo[count] - angVelo[count-1])/timeDelay;
//        angVelo[count - 1] = angVelo[count];
//    }
//    angVelo[count-1] = newAngle;
//    average += (angVelo[count-1] - angVelo[count-2])/timeDelay;
//    return average/averageWindow;
//}

// Main Loop for initialization, reading of UART buffer, and starting commands
int main(void)
{
    WDTCTL = WDTPW | WDTHOLD;   // stop watchdog timer

    // Configure Clocks
    CSCTL0 = 0xA500;                            // Write password to modify CS registers
    CSCTL1 = DCORSEL; // 16MHz    DCOFSEL0 + DCOFSEL1;                           // DCO = 8 MHz
    CSCTL2 |= SELM_3 + SELS_3 + SELA_3;         // MCLK = DCO, ACLK = DCO, SMCLK = DCO
    CSCTL3 |= DIVS_5;                           // Set divider for SMCLK (/32) -> SMCLK 500kHz

    // Configure timer B2 for DC Motor
//    TB2CTL |= TBSSEL_1 + MC_1 + TBIE + TBCLR;    // ACLK, up mode, overflow interrupt enable
//    TB2CTL &= ~TBIFG;
//    TB2CCR0 = 16000*timeDelay;                  // CCR0: control loop delay time 1ms

    // Configure timer B0 for Stepper Motor
    TB0CTL |= TBSSEL_1 + MC_1 + TBCLR;                  // ACLK, up mode (16MHz)
    TB0CCTL0 |= OUTMOD_4;                           // CCR0 interrupt enable
    TB0CCR0 = 1000; //timerVal;                           // CCR0: interrupt for half step phase switching

    P2DIR |= BIT1;
    P2SEL0 |= BIT1;
    P2SEL1 |= BIT1;

    // Pin 2.7 output High for ADC
//    P2DIR |= BIT7;
//    P2OUT |= BIT7;

    // Pin 1.3 for direction output
    P1DIR |= BIT3;

//    // Setup ADC
//    ADC10CTL0 &= ~ADC10ON;     // Turn off for editing
//    ADC10CTL0 |= ADC10SHT_2;     // Set as 10bit (1024)
//    ADC10CTL1 |= ADC10SHP;
//    ADC10MCTL0 |= ADC10INCH_12;
//
////    // Start Conversions
//    ADC10CTL0 |= ADC10ON + ADC10ENC + ADC10SC;
////    TA1CCTL0 &= ~CCIFG;
//    ADC10IE |= BIT0;
//    ADC10IFG &= ~ADC10IFG0;

    _EINT();                                //Global interrupt enable

    while (1);
    return 0;
}

// Timer B2 CCR1 Interrupt: Updates x Position and handles X Control Loop
//#pragma vector = TIMER2_B1_VECTOR
//__interrupt void ControlLoop(void){
//    if (avgAngVelo + angle < 0){
//        P1OUT |= BIT3;
//    }
//    else{
//        P1OUT &= ~BIT3;
//    }
//    double controlResponse = (Kp*abs(angle))+(Kw*abs(avgAngVelo));
//    if (abs(controlResponse) > 0.06){
////        TB0CTL |= MC_1;
//        timerVal = abs((8000000.0)/(controlResponse));
//        TB0CCR0 = timerVal;
//    }
////    else{
////        TB0CTL &= MC_0;
////    }
//    ADC10CTL0 |= ADC10SC;
//    TB2CTL &= ~TBIFG;                           // Reset interrupt flag
//}
//
////ADC ISR
//#pragma vector = ADC10_VECTOR
//__interrupt void ISR_ADC10_B(void)
//{
//    ADC10CTL0 &= ~ADC10ENC;
//    ADC10MCTL0 = ADC10INCH_12; //Convert from Channel 13 (Y)
//    x = ADC10MEM0;
//    angle = (x-zeroAngleOffset);
//    avgAngVelo = averageAngVelo(angle);
//    ADC10CTL0 |= ADC10ENC;//  + ADC10SC;
//    ADC10IFG &= ~ADC10IFG0; //RESET FLAG
//}


#include "adc_collector.h"
#include "event_detection.h"
/*
EVENT DETECTION MODULE:

	This function switches event_detected to 1 whenever an event is detected

*/

void detect_event(){
	event_detected= false;
	float gradient;	
	for(int i=1; i<WINDOW_SIZE; i++){
		gradient= 0.0;
		for(int j=0; j<NUM_ADC; j++){
				
			gradient+= 1;//((float)buffer[i][j] - (float)buffer[i-1][j]) / ((float)timer[i]-(float)timer[i-1]);
		}	
	}
	event_detected = (gradient > 100.0) ? true:false;
}

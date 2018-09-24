#include "adc_collector.h"
#include "event_detection.h"
/*
EVENT DETECTION MODULE:

This function switches event_detected 
to true whenever an event is detected
for a specific window of data

*/
void detect_event(){
	event_detected= false;
	uint64_t gradient;
	for(int i=1; i<WINDOW_SIZE; i++){
		gradient= 0;
		for(int j=0; j<NUM_ADC; j++){
			gradient+=(uint64_t)buffer[i][j]-(uint64_t)buffer[i-1][j];
		}
		gradient= (uint64_t)(gradient/NUM_ADC);
		event_detected=(gradient>100)?true:false;
	}
}

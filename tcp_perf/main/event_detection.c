#include "event_detection.h"
#include "adc_collector.h"

/*
EVENT DETECTION MODULE:

	This function switches event_detected to 1 whenever an event is detected

*/
void detect_event(){
	event_detected= 1;	
}

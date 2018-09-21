#ifndef __ADC_COLLECTOR_H__
#define __ADC_COLLECTOR_H__

#ifdef __cplusplus
extern "C" {
#endif

volatile int event_detected;

void detect_event();
#endif

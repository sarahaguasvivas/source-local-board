#ifndef __EVENT_DETECTION_H__
#define __EVENT_DETECTION_H__

#ifdef __cplusplus
extern "C" {
#endif

volatile bool event_detected;
//volatile uint16_t gradient;
void detect_event();
#endif

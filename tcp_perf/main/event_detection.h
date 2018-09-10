#ifndef __ADC_COLLECTOR_H__
#define __ADC_COLLECTOR_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "esp_adc_cal.h"

volatile uint16_t intense;

volatile bool yesno;

volatile uint32_t timer_click_count;

void detect_event(float * signal);
#endif

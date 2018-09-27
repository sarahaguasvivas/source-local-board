#ifndef __ADC_COLLECTOR_H__
#define __ADC_COLLECTOR_H__

#ifdef __cplusplus
extern "C" {
#endif

#define WINDOW_SIZE		250	
#define NUM_ADC			4 //it is actually 3 adcs and one flag	
#define V_REF			1200
#include "esp_adc_cal.h"
//#include "event_detection.h"
volatile int16_t buffer[WINDOW_SIZE][NUM_ADC];
volatile uint32_t timer[WINDOW_SIZE];
volatile int16_t gradient;
volatile bool event_detected;
float* data_buffer;//4B
char* tcp_buffer;//1B
//float * timer;

volatile int buffer_idx;
volatile bool buffer_full;
volatile int timer_idx;
static intr_handle_t s_timer_handle;
volatile uint32_t timer_click_count;

esp_adc_cal_characteristics_t adc_characteristics;

void init_timer(int timer_period_us);
void init_buffer();
void init_adcs();
void measure_adcs();

#endif

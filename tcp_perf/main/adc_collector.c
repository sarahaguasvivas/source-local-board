#include <stddef.h>
#include "esp_intr_alloc.h"
#include "esp_attr.h"
#include "driver/timer.h"
#include "esp_log.h"
#include "esp_err.h"
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_system.h"
#include "esp_spi_flash.h"
#include "esp_adc_cal.h"

#include "driver/gpio.h"
#include "driver/adc.h"
#include "time.h"
#include "sys/time.h" 
#include "adc_collector.h" // The data buffer will consist of 8 bytes of data for each entry in the buffer (4 sensors, 16-bit values) // The data is stored ADC0, ADC1, ADC2, ADC3
#define ADC_5   ADC1_CHANNEL_5
#define ADC_6 	ADC1_CHANNEL_6

static void timer_isr(void* arg)
{
    // This resets the timer interrupt -- don't mess with this unless you
    // know what you're doing or want to break things
	TIMERG0.int_clr_timers.t0 = 1;
	TIMERG0.hw_timer[0].config.alarm_en = 1;
	
	// code which runs in the interrupt	
	if(!buffer_full)
	{
		measure_adcs();
	}
}

// This is going to set up a hardware interrupt.  Again, don't mess with this
// unless you want to break things, or you know what you're doing.
void init_timer(int timer_period_us)
{
	timer_config_t config = {
		.alarm_en = true,
		.counter_en = false,
		.intr_type = TIMER_INTR_LEVEL,
		.counter_dir = TIMER_COUNT_UP,
		.auto_reload = true,
		.divider = 80			/* 1 us per tic */
	};

	timer_init(TIMER_GROUP_0, TIMER_0, &config);
	timer_set_counter_value(TIMER_GROUP_0, TIMER_0, 0);
	timer_set_alarm_value(TIMER_GROUP_0, TIMER_0, timer_period_us);
	timer_enable_intr(TIMER_GROUP_0, TIMER_0);
	timer_isr_register(TIMER_GROUP_0, TIMER_0, &timer_isr, NULL, 0, &s_timer_handle);

	timer_start(TIMER_GROUP_0, TIMER_0);
}


void init_buffer()
{
    // Want to be able to write to data_buffer as a float
	data_buffer = (float*) malloc (WINDOW_SIZE * NUM_ADC * sizeof(float));
    // The tcp_send function reads off bytes -- this is an easy way to convert the
    // data_buffer from a float array to a byte array without affect data content
    tcp_buffer = (char*) data_buffer;

    // We start at index 0, and the buffer isn't full yet.
	buffer_idx = 0;
	buffer_full = false;
//	buffer_onetwo= true;
}


void init_adcs()
{
	adc1_config_width(ADC_WIDTH_BIT_12);
	adc1_config_channel_atten(ADC_5, ADC_ATTEN_DB_11);
	adc1_config_channel_atten(ADC_6, ADC_ATTEN_DB_11);

//	esp_adc_cal_get_characteristics(V_REF, ADC_ATTEN_DB_11, ADC_WIDTH_BIT_12, &adc_characteristics);
}


void measure_adcs()
{
// ESP_LOGI(TAG, "got ip:%s\n",
// 60                  ip4addr_ntoa(&event->event_info.got_ip.ip_info.ip)); 
	uint32_t adc0_val, adc1_val;

	// Measure the ADCs
	adc0_val = adc1_get_raw(ADC_5);
	adc1_val = adc1_get_raw(ADC_6);

	// Write to the mesaurement window
	buffer[buffer_idx][0] = (uint16_t) adc0_val;
	buffer[buffer_idx][1] = (uint16_t) adc1_val;
	
	buffer_idx += NUM_ADC;
	if(buffer_idx >= WINDOW_SIZE)
	{
		buffer_full = true;
	}
}



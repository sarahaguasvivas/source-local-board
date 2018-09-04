deps_config := \
	/Users/sarahaguasvivas/esp/esp-idf/components/app_trace/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/aws_iot/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/bt/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/esp32/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/ethernet/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/fatfs/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/freertos/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/heap/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/libsodium/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/log/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/lwip/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/mbedtls/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/openssl/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/pthread/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/spi_flash/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/spiffs/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/tcpip_adapter/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/wear_levelling/Kconfig \
	/Users/sarahaguasvivas/esp/esp-idf/components/bootloader/Kconfig.projbuild \
	/Users/sarahaguasvivas/esp/esp-idf/components/esptool_py/Kconfig.projbuild \
	/Users/sarahaguasvivas/esp/tcp_perf/main/Kconfig.projbuild \
	/Users/sarahaguasvivas/esp/esp-idf/components/partition_table/Kconfig.projbuild \
	/Users/sarahaguasvivas/esp/esp-idf/Kconfig

include/config/auto.conf: \
	$(deps_config)


$(deps_config): ;

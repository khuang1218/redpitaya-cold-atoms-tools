/* Red Pitaya C API example Generating continuous signal  
 * This application generates a specific signal */

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include "redpitaya/rp.h"

int main(int argc, char **argv){
	if(argc<5){
	printf("some argument are missing, the program will be closed\n");
	exit(0);
	}
	float Starting_amplitude = 0.1;
	float Ramp_time = 50;
	float SF_dc = 0.02;
	float Amplitude = Starting_amplitude;
	float Offset=0;
	float feq=7000.0;
	int   waveform = 0;
	/* Print error, if rp_Init() function failed */
	if(rp_Init() != RP_OK){
		fprintf(stderr, "Rp api init failed!\n");
	}
	uint32_t buff_size = 1;
	float *buff = (float *) malloc (buff_size * sizeof(float));
	Starting_amplitude = atof(argv[1]);
	if(Starting_amplitude < -1 || Starting_amplitude > 1){
	printf("Starting amplitude out of range [-1:1]\n");
	exit(0);
	}
	Ramp_time = atof(argv[2]);
	if(Ramp_time < 6){
	printf("Ramping time out range, [6:]\n");
	exit(0);
	}
	SF_dc = atof(argv[3]);
	if(SF_dc < -1 || SF_dc > 1){
	printf("dc is out of range [-1:1]\n");
	exit(0);
	}
	feq = atof(argv[4]);
	waveform = atoi(argv[5]);
	if(waveform < 0 || waveform > 3){
	printf("waveform out of range, the possible values are:\n");
	printf("0 for triangular waveform\n");
	printf("1 for sine waveform\n");
	printf("2 for rump up waveform\n");
	printf("3 for rump down waveform\n");
	exit(0);
	}
	float DC_step = SF_dc/(Starting_amplitude/0.01);
	float step_time = (Ramp_time-6.0)*1000.0/(Starting_amplitude/0.01);
//	printf("%f\n", step_time);

	/* Generating frequency */
	rp_GenFreq(RP_CH_1, feq);

	/* Generating wave form */
	switch(waveform){

	case 0:	rp_GenWaveform(RP_CH_1, RP_WAVEFORM_TRIANGLE);
		break;
	case 1:	rp_GenWaveform(RP_CH_1, RP_WAVEFORM_SINE);
		break;
	case 2:	rp_GenWaveform(RP_CH_1, RP_WAVEFORM_RAMP_UP);
		break;
	case 3:	rp_GenWaveform(RP_CH_1, RP_WAVEFORM_RAMP_DOWN);
		break;
	}
	while (1) {
		Offset=0;
		rp_GenOffset(RP_CH_1, Offset);
		rp_AcqReset();
		rp_AcqSetDecimation(1);
		rp_AcqSetTriggerDelay(0);
		rp_AcqStart();
		/* Generating amplitude */
		rp_GenAmp(RP_CH_1, Amplitude);
		/* Enable channel */
		rp_GenOutEnable(RP_CH_1);
		usleep(10000);

		rp_AcqSetGain(RP_CH_1, RP_HIGH );

		while (1) {
			usleep(10);
			rp_AcqGetOldestDataV(RP_CH_1, &buff_size, buff);
//			printf("%f\n", buff[0]);
			if(buff[0]>0.5)
			{
				break;
			}
		}
		/* amplitude slope */
		while (Amplitude > 0.01) {
			Amplitude -= 0.01;
			Offset += DC_step;
			rp_GenAmp(RP_CH_1, Amplitude);
			rp_GenOffset(RP_CH_1, Offset);
			usleep(step_time);

		}

		Amplitude = 0.0;
		rp_AcqReset();
		rp_AcqSetTriggerDelay(0);
		rp_AcqSetDecimation(1);
		rp_AcqStart();
		rp_AcqSetGain(RP_CH_1, RP_HIGH );

		while (1) {
			usleep(10);
			rp_AcqGetOldestDataV(RP_CH_1, &buff_size, buff);
//			printf("%f\n", buff[0]);
			if(buff[0]<0.5)
			{
				break;
			}
		}
		Amplitude = Starting_amplitude;
		usleep(1000);
		rp_AcqReset();
	}

	/* Releasing resources */
	free(buff);
	rp_Release();

	return 0;
}

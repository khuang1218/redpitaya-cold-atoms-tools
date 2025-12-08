/* Red Pitaya C API example Acquiring a signal from a buffe
 * This application acquires a signal on a specific channel */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "redpitaya/rp.h"
//#include <time.h>
//#include "redpitaya/rp.h"
//#include <pool.h>


float Pid(float error, float integral, float Kp, float Ki){
	float output;
	output=(float)error*Kp;
	output+=integral*Ki;
	return output;
	}


int main(int argc, char **argv){
        /* Print error, if rp_Init() function failed */
        if(rp_Init() != RP_OK){
                fprintf(stderr, "Rp api init failed!\n");
        }
	bool peak[3]={0,0,0};
	int peak_pos[3]={0,0,0};
	float frequency = 1.0;
    int delay = 8192;
	int pau = 90000;
	//bool on_off=1;
	float trig =0;
	float Dc[]={0.9,0.0};
	float Kp[]={0.0,0.0};
	float Ki[]={0.0,0.0};
	int set_point[]={0,0};
	int integral[]={0,0};
	float error[]=0;
	int loop=0;
	float relative_pos_peak[]={0};
	float relative_pos_set[]={0};
	//time_t start,actual;
	//int cicle_count=0;
	/*-------------------------------------------------
	int fd =0;
	char biff[10];
	struct pollfd fds[1];
	int  timeout;
	/*-------------------------------------------------*/
	//start=time(NULL);
//	float treshold = 0.2;
	if(argc > 1){delay=atof(argv[1]);}
	if(argc > 2){pau=atof(argv[2]);}
	if(argc > 3){set_point[0]=atof(argv[3]);}
	if(argc > 4){Kp[0]=atof(argv[4]);}
	if(argc > 5){Ki[0]=atof(argv[5]);}
	if(argc > 6){Dc[0]=atof(argv[6]);}
	if (argc > 7) {set_point[1] = atof(argv[7]);}
	if(argc > 8){Kp[1]=atof(argv[8]);}
	if(argc > 9){Ki[1]=atof(argv[9]);}
	if(argc > 10){Dc[1]=atof(argv[10]);}
	if(argc > 11) {loop=atof(argv[11]);}
	//if(argc > 11){set_point[2]=atof(argv[11])-set_point[0];}
	//if(argc > 12){Kp[2]=atof(argv[12]);}
	//if(argc > 13){Ki[2]=atof(argv[13]);}
	//if(argc > 14){Dc[2]=atof(argv[14]);}
	//if(argc > 15){loop=atof(argv[15]);}
//	printf("%i\n",loop);
//	loop=0;
	int status = rp_AOpinSetValue(0,Dc[0]);
		if(status!= RP_OK){printf("problem with the analog output");}
//	printf("%i\n",delay);

        /*LOOB BACK FROM OUTPUT 2 - ONLY FOR TESTING*/
	rp_GenReset();
        rp_GenFreq(RP_CH_1, frequency);
        rp_GenFreq(RP_CH_2, frequency);
        rp_GenAmp(RP_CH_1, 0);
        rp_GenAmp(RP_CH_2, 0);
	rp_GenOffset(RP_CH_1,Dc[1]);
	//rp_GenOffset(RP_CH_2,Dc[2]);
        rp_GenWaveform(RP_CH_1, RP_WAVEFORM_RAMP_UP);
        rp_GenWaveform(RP_CH_2, RP_WAVEFORM_SQUARE);
        rp_GenOutEnable(RP_CH_1);
        rp_GenOutEnable(RP_CH_2);

	FILE *fp;
	//FILE *fg;
	//fp = fopen("double_lock_off.txt","w");
	fp = fopen("Test2.dat","w");
    uint32_t buff_size = 6000;
    float *buff = (float *)malloc(buff_size * sizeof(float));
    int *del = (int *)malloc(sizeof(int));
    unsigned int *pos = (unsigned int *)malloc(sizeof(int));
do{

	rp_AcqReset();
	rp_AcqSetDecimation(RP_DEC_64);
	//rp_AcqSetTriggerLevel(RP_CH_2, 0);
	rp_AcqSetTriggerDelay(delay);
	rp_AcqGetTriggerDelay(del);
	rp_AcqGetWritePointerAtTrig(pos);

	rp_AcqStart();


    /* After acquisition is started some time delay is needed in order to acquire fresh samples in to buffer*/
    /* Here we have used time delay of one second but you can calculate exact value taking in to account buffer*/
    /*length and smaling rate*/

    rp_AcqSetTriggerSrc(RP_TRIG_SRC_EXT_PE);
    rp_acq_trig_state_t state = RP_TRIG_STATE_WAITING;
	rp_AcqGetWritePointerAtTrig(pos);
//	printf("%i\n%i\n",del[0],pos[0]);

    while(1){
			rp_AcqGetTriggerState(&state);
            if(state == RP_TRIG_STATE_TRIGGERED){
            break;
            }
	}
	usleep(pau);

    rp_AcqGetOldestDataV(RP_CH_1, &buff_size, buff);
	float der;
    int i;
    for(i = 0; i < buff_size-2; i++){
			der=10*(buff[i+2]-buff[i]);
		    if(der<-0.005 && buff[i]>0.04){trig=0.06;}
					else{trig=0;}
		    if(peak[0]==0){
					if(trig>0){peak[0]=1,peak_pos[0]=i;}
							}
		    else{if(peak[1]==0){
							if((i-peak_pos[0])>300&&peak[1]==0&&trig>0){peak[1]=1,peak_pos[1]=i;}
				            }else{
							if((i-peak_pos[1])>300&&peak[2]==0&&trig>0){peak[2]=1,peak_pos[2]=i;}
							}
			}
			fprintf(fp, "%i %f %f %f\n", i, buff[i], der, trig);
	}
	system("gnuplot gnuplot_setting2.gn");
	rewind(fp);
	int k=0;
	int distance=peak_pos[2]-peak_pos[0];
			error=peak_pos[k]-set_point[0];
			integral[k]+=error;
			Dc[k]+=Pid(error,integral[k],Kp[k],Ki[k]);
			status=rp_AOpinSetValue(0,Dc[k]);
			if(status!= RP_OK){printf("problem with the analog output");}
	for (k = 1; k < 2; k++) {
			relative_pos_set[k - 1] = (float)set_point[k] / (float)distance;
			relative_pos_peak[k - 1] = ((float)peak_pos[k] / (float)distance;
			error = relative_pos_peak[k - 1] - relative_pos_set[k - 1];
			integral[k]+=error[k];

			Dc[k] += Pid(error, integral[k], Kp[k], Ki[k]);
			rp_GenOffset(RP_CH_1, Dc[1]);
			}

//	printf("%i %ld\n",cicle_count,actual);
	printf("%i %i %i \n",peak_pos[0],peak_pos[1],peak_pos[2]);
//	printf("%f %f %f\n",error[0],error[1],error[2]);
	printf("%f %f \n",Dc[0],Dc[1]);
//	fprintf(fp,"%i\t%ld\t%i\t%i\t%i\t%i\t%f\t%f\t%f\t%f\t%f\t%f\n",cicle_count,actual,peak_pos[0],peak_pos[1],peak_pos[2],peak_pos[3],error[0],error[1],error[2],Dc[0],Dc[1],Dc[2]);
	peak_pos[0]=peak_pos[1]=0;
	peak[0]=peak[1]=peak[2]=peak[3]=0;

	/* BREAKING OPTION */

	if(Dc[0]<-1 || Dc[0]>1) {
		printf("dc0 out of range");
		break;
		}
	if(Dc[1]<-1 || Dc[1]>1){
		printf("dc1 out of range");
		break;
		}
	if(Dc[2]<-1 || Dc[2]>1){
		printf("dc2 out of range");
		break;
		}

      }while(loop);

	/* Releasing resources */

	free(buff);
	fclose(fp);
        rp_Release();
        return 0;
}
        

#pragma once
#ifndef VZ_CALIBRATION_H
#define VZ_CALIBRATION_H
#define AVS_CHAR_LEN 128
#ifdef __cplusplus //C++环境时，执行extern "C" { }
extern "C" {
#endif

	__declspec(dllexport) int Model_Calibration(char config_file[AVS_CHAR_LEN]);

	__declspec(dllexport) int X2_lut_generate(char CalFileln[255], char mesh_file_prefix[255]);//双目lut生成

	__declspec(dllexport) int FG_lut_generate(char CalFileln[255], char mesh_file_prefix[255]);//三目lut生成

	__declspec(dllexport) bool rotate_and_resize_images(char image_path[1024]);
#ifdef __cplusplus
}
#endif


#endif // !X2_CALIBRATION_H
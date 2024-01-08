/*
  Copyright (c), 2001-2021, Shenshu Tech. Co., Ltd.
 */

#ifndef __MPI_AVS_CALIBRATION_H__
#define __MPI_AVS_CALIBRATION_H__

#ifdef __cplusplus
#if __cplusplus
extern "C" {
#endif /* __cplusplus */
#endif /* __cplusplus */

/* if using dynamic linking library, AVS_DLLEXPORT should be defined */
#ifdef AVS_DLLEXPORT
/* DLLEXPORT has already defined,nothing to do */
#else
#define AVS_DLLEXPORT __declspec(dllexport)
#endif

#define AVS_CHAR_LEN 128

/* specification of the LUT accuracy */
typedef enum {
    AVS_LUT_ACCURACY_HIGH = 0,
    AVS_LUT_ACCURACY_LOW,
    AVS_LUT_ACCURACY_BUTT
} avs_lut_accuracy;

/* the status of avs interface returned */
typedef enum {
    AVS_EOF = -1, /* internal error codes */
    AVS_OK = 0,   /* success */

    /* error statuses */
    AVS_UNABLE_TO_FIND_OVERLAP,
    AVS_FILE_READ_ERROR,
    AVS_FILE_WRITE_ERROR,
    AVS_FILE_INVALID,
    AVS_ALLOC_FAILED,
    AVS_INVALID_PARAM,

    AVS_STATUS_BUTT
} avs_cal_status;

typedef enum {
    AVS_TYPE_AVSP = 0,
    AVS_TYPE_PTGUI,
    AVS_TYPE_HUGIN,
    AVS_TYPE_BUTT
} avs_type;

/*
 * stores the measurement used to determine whether a good calibration has been
 * achieved. average_reprojection_err: this is the mean re-projection error in
 * pixels.  the re-projection error is the distance in pixels from the estimated
 * point projected into the camera and the detected image point. The calibration
 * has failed if this is greater than 3 pixels. max_reprojection_err: This is
 * the maximum re-projection error in pixels. The calibration has failed if this
 * is greater than 20 pixels. total_matched_points: this is the total number of
 * points which have not been rejected by the end of the optimisation process.
 * Each calibration frame adds W*H points where the board shape is (W, H).
 */
typedef struct {
    double max_reprojection_err;
    double average_reprojection_err;
    double total_matched_points;
} avs_calibration_measurement;

/*
 * production calibration configuration structure
 * camera_num: the number of input cameras,range is 2 to 8
 * fixture_radius: The nominal radius of the production calibration fixture from
 * the centre of the image sensors. color_chessboard_flag: whether the input
 * image is color chessboard. image:    The images of calibration file captured
 * from each camera.
 */
typedef struct {
    unsigned int camera_num;
    float fixture_radius;
    int color_chessboard_flag;
    const char **image;
} avs_calibration_cfg;

/*
 * lut from calibration configuration structure
 * pc_calibration_file:  Path to the calibration_file (output of avs_cal or a
 * pto file) stitch_distance:      The radius of the sphere used to create
 * points to sample from. Stitching will be performed correctly at this
 * distance.  (Ignored if calibration from PTGui.) lut_accuracy:         The
 * accuracy of the lookup table. Valid value is 0 or 1. avs_type: Type selection
 * of calibration file, AVS_TYPE_AVSP is for avs_cal, AVS_TYPE_PTGUI is from
 * PTGui.
 */
typedef struct {
    const char *file;
    float stitch_distance;
    avs_lut_accuracy lut_accuracy;
    avs_type avs_type;
} avs_lut_from_calibration_cfg;

/*
 * gets the version number for this library
 * return the lib version
 */
AVS_DLLEXPORT int mpi_avs_version(char avs_calibration_version[AVS_CHAR_LEN]);

/*
 * Generates the camera model and geometries from sets of calibration frames.
 * config_file: the yaml input config file.
 * result:      Reference to the structure to store the measurement of how
 * accurate the calibration is.
 */
AVS_DLLEXPORT avs_cal_status mpi_avs_model_calibration(const char *config_file, avs_calibration_measurement &result);

/*
 * Generates the lookup table from the output of avs_cal fuction
 * lut_from_calib_cfg:     Input configuration for lut from calibraiton.
 * mask_prefix:            Defines the masks used for each camera. Camera at
 * index n will use the mask with filename prefix_n.png.
 * These indicies are 1 based. The mask should be the same
 * size as the frame for this camera. White pixels in the
 * mask are present and black pixels are not present. For
 * a standard full frame image a fully white image will be
 * used. For a circular fisheye, a white circle covering
 * the valid pixels will be used.
 * output_prefix:          Defines the filename of the output lookup tables. The
 * output filename for camera n will be prefix_n.bin
 */
AVS_DLLEXPORT avs_cal_status mpi_avs_lut_from_calibration(avs_lut_from_calibration_cfg *cfg, const char *mask_prefix,
    const char *output_prefix);

/*
 * avs calibration function.
 * calib_cfg:   Input configuration for avs production calibration.
 * input_file:  Input calibration file
 * output_file: Output calibration file
 * result:      Output reference to the structure of the accuracy measurement of
 * calibration.
 */
AVS_DLLEXPORT avs_cal_status mpi_avs_calibration(avs_calibration_cfg *cfg, const char *input_file,
    const char *output_file, avs_calibration_measurement &result);

    /* 
     * avs production calibration from sets of chessboard images.
     * config_file: input configuration for chessboard calibration
     * result: output measurement
     * output_error_flag: output error flag
     */
    AVS_DLLEXPORT avs_cal_status mpi_avs_chessboard_calibration(const char *config_file,
        avs_calibration_measurement &result, int &output_error_flag);

#ifdef __cplusplus
#if __cplusplus
}
#endif /* __cplusplus */
#endif /* __cplusplus */

#endif /* mpi_avs_calibration.h */
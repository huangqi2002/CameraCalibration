#ifndef OT_MPI_STITCH_LUT_GENERATE_H
#define OT_MPI_STITCH_LUT_GENERATE_H

#include "ot_type.h"

#ifdef __cplusplus
extern "C" {
#endif

#define CHAR_LEN 256
#define FILE_NAME_SIZE 255
#define GDC_MAX_STITCH_NUM 4
#define FILE_HEADER_SIZE 100

typedef enum {
    OT_LUT_CELL_SIZE_16,
    OT_LUT_CELL_SIZE_32,
    OT_LUT_CELL_SIZE_64,
    OT_LUT_CELL_SIZE_128,
    OT_LUT_CELL_SIZE_256,
    OT_LUT_CELL_SIZE_BUTT
} ot_lut_cell_size;

typedef struct {
    int x;
    int y;
} ot_point;

typedef struct {
    td_u32 width;
    td_u32 height;
} ot_size;

typedef enum {
    PROJECTION_EQUIRECTANGULAR = 0, /* Equirectangular mode. */
    PROJECTION_RECTILINEAR = 1,     /* Rectilinear mode. */
    PROJECTION_CYLINDRICAL = 2,     /* Cylindrical mode. */
    PROJECTION_BUTT
} projection_mode;

typedef struct {
    ot_size in_size;            /* lut image in size */
    ot_size out_size;           /* lut image out size */
    ot_size mesh_size;          /* lut size, added for pqtools */
    ot_lut_cell_size cell_size; /* lut cell size */
    td_u32 lut_len;             /* length of lut, length = stride * mesh_height */
    ot_point *mesh_points;      /* lut point */
} stitch_lut;

typedef struct {
    int fov_x; /* Range: [1000, 36000]; Horizontal FOV. */
    int fov_y; /* Range: [1000, 18000]; Vertical FOV. */
} stitch_fov;

typedef struct {
    int yaw;   /* Range: [-18000, 18000]; Yaw angle. */
    int pitch; /* Range: [-18000, 18000]; Pitch angle. */
    int roll;  /* Range: [-18000, 18000]; Roll angle. */
} stitch_rotation;

typedef struct {
    int camera_num;               /* camera number */
    ot_size src_size;             /* Range: [256, 8192]; Size of source image. */
    ot_size dst_size;             /* Range: [256, 8192]; Size of target image. */
    projection_mode prj_mode;     /* Projection mode. */
    ot_point center;              /* Range: [-16383,16383]: Center point. */
    stitch_fov fov;               /* Output FOV. */
    stitch_rotation ori_rotation; /* Output original rotation. */
    stitch_rotation rotation;     /* Output rotation. */
} stitch_avs_config;

/*
 * Specification of calibration file type
 * TYPE_AVSP:  calibration
 * file come from AVSP calibration
 * TYPE_PTGUI: calibration file come from
 * PTGUI calibration
 * TYPE_HUGIN: calibration file come from HUGIN
 * calibration
 * TYPE_BUTT:  reserved.
 */
typedef enum {
    TYPE_AVSP = 0,
    TYPE_PTGUI,
    TYPE_HUGIN,
    TYPE_BUTT
} stitch_cal_type;

/*
 * Specification of fine tuning for each camera.
 * adjust_en: the
 * enable of fine tuning for each camera.
 * yaw:       the yaw-direction
 * adjustment for each camera.
 * pitch:     the pitch-direction adjustment
 * for each camera.
 * roll:      the roll-direction adjustment for each
 * camera.
 * offset_x:  the X-direction adjustment for each camera.
 *
 * offset_y:  the Y-direction adjustment for each camera.
 */
typedef struct {
    td_bool adjust_en;
    int yaw;      /* range: [-18000, 18000]; yaw angle. */
    int pitch;    /* range: [-18000, 18000]; pitch angle. */
    int roll;     /* range: [-18000, 18000]; roll angle. */
    int offset_x; /* range: [-width/2*100, width/2*100]; x offset. */
    int offset_y; /* range: [-height/2*100, height/2*100]; y offset. */
} stitch_adjust;

/*
     * Specification of fine tuning.
     * fine_tuning_en: the enable of
 * fine tuning function.
     * adjust:         the adjustment for each camera.

 */
typedef struct {
    td_bool fine_tuning_en;
    stitch_adjust adjust[GDC_MAX_STITCH_NUM];
} stitch_fine_tuning;

/*
     * the input  of lut generate function.
     * type:            input
 * calibration file type
     * cal_file_name:   file address of input
 * calibration file.
     * stitch_distance: the radius of the sphere used to
 * create points to sample from.
     *                  stitching will be
 * performed correctly at this distance.  (ignored if calibration from pt_gui.)

 * * fine_tuning_cfg: pitch/yaw/roll/xoffset/yoffset for each camera
     */
typedef struct {
    stitch_cal_type type;
    char *cal_file_name;
    float stitch_distance;
    stitch_fine_tuning fine_tuning_cfg;
} stitch_lut_generate_input;

typedef struct {
    stitch_avs_config avs_stitch_config;
    stitch_lut_generate_input lut_input;
} stitch_config;

typedef struct {
    ot_point left_point[GDC_MAX_STITCH_NUM];
    ot_point right_point[GDC_MAX_STITCH_NUM];
} stitch_img_size_cfg;

typedef struct {
    stitch_lut lut[GDC_MAX_STITCH_NUM];
    ot_point overlap_point[GDC_MAX_STITCH_NUM][2]; /* 2 images stitching£¬only
                                                      overlap_point[1][0].x is
                                                      valid */
} stitch_out_param;

/* ot_mpi_stitch_lut_generate: output lut for gdc tranform and stitch param
 * stitch_cfg: input stitch tuning info
 * size_cfg: input param for lut generate, crop area(x coordinates) is needed
 * out_param: output lut and params
 * mesh_file_name: output lut file name address
 */
__declspec(dllexport) int ot_mpi_stitch_lut_generate(const stitch_config *stitch_cfg,
    const stitch_img_size_cfg *size_cfg, stitch_out_param *out_param, const char *mesh_file_prefix);

/* mpi_stitch_get_debug_info: print debug information */
__declspec(dllexport) int mpi_stitch_get_debug_info(char info[CHAR_LEN]);

#ifdef __cplusplus
}
#endif

#endif /* OT_MPI_STITCH_LUT_GENERATE_H */

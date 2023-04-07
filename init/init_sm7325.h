#ifndef INIT_SM7325_H
#define INIT_SM7325_H

#include <string.h>

enum device_variant {
    VARIANT_A528B = 0,
    VARIANT_A528N,
    VARIANT_MAX
};

typedef struct {
    std::string model;
    std::string codename;
} variant;

static const variant international_models = {
    .model = "SM-A528B",
    .codename = "a52sxq"
};

static const variant asia_models = {
    .model = "SM-A528N",
    .codename = "a52sxq"
};

static const variant *all_variants[VARIANT_MAX] = {
    &international_models,
    &asia_models
};

#endif // INIT_SM7325_H

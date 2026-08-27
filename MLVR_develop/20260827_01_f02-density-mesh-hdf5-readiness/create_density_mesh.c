#include <hdf5.h>
#include <stdio.h>

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  const hsize_t boundary_dims[2] = {3, 2};
  const hsize_t bins_dims[1] = {3};
  const hsize_t density_dims[3] = {2, 1, 1};
  const double boundary[3][2] = {{-5.0, 5.0}, {-5.0, 5.0}, {-5.0, 5.0}};
  const double bins[3] = {2.0, 1.0, 1.0};
  const double density[2][1][1] = {{{0.5}}, {{2.0}}};
  hid_t file = H5Fcreate(argv[1], H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
  hid_t geometry = H5Gcreate2(file, "Geometry", H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
  hid_t attribute_space = H5Screate(H5S_SCALAR);
  int mesh_type = 1;
  hid_t attribute = H5Acreate2(geometry, "MeshType", H5T_NATIVE_INT, attribute_space, H5P_DEFAULT, H5P_DEFAULT);
  H5Awrite(attribute, H5T_NATIVE_INT, &mesh_type);
  H5Aclose(attribute);
  H5Sclose(attribute_space);
  hid_t boundary_space = H5Screate_simple(2, boundary_dims, NULL);
  hid_t boundary_set = H5Dcreate2(geometry, "Boundary", H5T_NATIVE_DOUBLE, boundary_space, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
  H5Dwrite(boundary_set, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, boundary);
  H5Dclose(boundary_set);
  H5Sclose(boundary_space);
  hid_t bins_space = H5Screate_simple(1, bins_dims, NULL);
  hid_t bins_set = H5Dcreate2(geometry, "BinNumber", H5T_NATIVE_DOUBLE, bins_space, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
  H5Dwrite(bins_set, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, bins);
  H5Dclose(bins_set);
  H5Sclose(bins_space);
  hid_t density_space = H5Screate_simple(3, density_dims, NULL);
  hid_t density_set = H5Dcreate2(file, "density", H5T_NATIVE_DOUBLE, density_space, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
  H5Dwrite(density_set, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, density);
  H5Dclose(density_set);
  H5Sclose(density_space);
  H5Gclose(geometry);
  H5Fclose(file);
  return 0;
}

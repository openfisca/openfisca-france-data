# To install rhdf5
# source("http://bioconductor.org/biocLite.R")
# biocLite("rhdf5")
library(rhdf5)
library("StatMatch")  
args = commandArgs()
temporary_store_directory = args[length(args)]
temporary_store_directory

# https://github.com/pydata/pandas/issues/9636
loadhdf5data <- function(h5File) {  
  listing <- h5ls(h5File)
  # Find all data nodes, values are stored in *_values and corresponding column
  # titles in *_items
  data_nodes <- grep("_values", listing$name)
  name_nodes <- grep("_items", listing$name)
  
  data_paths = paste(listing$group[data_nodes], listing$name[data_nodes], sep = "/")
  name_paths = paste(listing$group[name_nodes], listing$name[name_nodes], sep = "/")
  
  columns = list()
  for (idx in seq(data_paths)) {
    # data <- data.frame(t(h5read(h5File, data_paths[idx], bit64conversion="int")))
    data <- data.frame(t(h5read(h5File, data_paths[idx])))
    # names <- t(h5read(h5File, name_paths[idx], bit64conversion="int"))
    names <- t(h5read(h5File, name_paths[idx]))
    entry <- data.frame(data)
    colnames(entry) <- names
    columns <- append(columns, entry)
  }
  
  data <- data.frame(columns)
  
  return(data)
}

logement = loadhdf5data(file.path(temporary_store_directory ,"logement_imputation.h5"))
erf = loadhdf5data(file.path(temporary_store_directory ,"erf_imputation.h5"))

allvars = c('statut_occupation', 'hnph2', 'iaat_bis', 'mdiplo', 'mtybd', 'tu99_recoded', 'magtr', 'mcs8', 'deci')
classes = c('tu99_recoded', 'deci')
matchvars = setdiff(allvars, classes)
out.nnd = NND.hotdeck(
  data.rec = erf,
  data.don = logement,
  match.vars = matchvars,
  don.class = classes,
  dist.fun = "Gower",
)

fill_erf_nnd = create.fused(
  data.rec = erf,
  data.don = logement,
  mtc.ids = out.nnd$mtc.ids,
  z.vars = "lmlm",
)

h5save(fill_erf_nnd, file = file.path(temporary_store_directory ,"imputation.h5"))
H5close()

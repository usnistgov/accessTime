rm(list=ls())
library(accessTime)
library(dplyr)
setwd(dirname(sys.frame(1)$ofile))
#--------------------[Helper functions]----------------------
ref_word_csv <- function(sut_fit, name){
  coefs <- sapply(sut_fit, coef)
  vcovs <- sapply(sut_fit, vcov)
  rownames(vcovs) <- c("t0_t0", "lambda_t0", "t0_lambda", "lambda_lambda")
  res <- cbind(t(coefs), t(vcovs))
  write.csv(res, name, quote=FALSE)
}

# ref_tech_csv <- function(tech_fits, name){
#   coefs <- sapply(tech_fits, coef)
#   vcovs <- sapply(tech_fits, )
# }

rec_access_csv <- function(tech_fits, name){
  alpha <- seq(from=0.5, to=0.99, by=0.01)
  access_vals_raW <- lapply(tech_fits,
               function(x){
                 eval_access(x, alpha)
               })
  access_vals <- bind_rows(access_vals_raW, .id="Technology")
  write.csv(access_vals, name, quote=FALSE, row.names=FALSE)
}
#--------------------[PTT Gate results]-----------------------
data_path <- file.path("data", "reference_data")
ref_word_csv(ptt_gate, file.path(data_path, "PTT-gate-word-fits.csv"))

tech_fits <- list(analog_direct=analog_direct,
                  p25_direct=p25_direct,
                  p25_trunked_phase1=p25_trunked_phase1,
                  p25_trunked_phase2=p25_trunked_phase2,
                  lte=lte
                  )

rec_access_csv(tech_fits, file.path(data_path, "reference-access-values.csv"))
ref_word_csv(tech_fits, file.path(data_path, "reference-tech-fits.csv"))

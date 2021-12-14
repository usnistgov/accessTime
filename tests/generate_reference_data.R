library(accessTime)
library(dplyr)
setwd(dirname(sys.frame(1)$ofile))
#--------------------[Helper functions]----------------------
ref_word_csv <- function(sut_fit, name){
  coefs <- sapply(sut_fit, coef)
  vcovs <- sapply(sut_fit, vcov)
  rownames(vcovs) <- c("t0, t0", "lambda, t0", "t0, lambda", "lambda, lambda")
  res <- cbind(t(coefs), t(vcovs))
  write.csv(res, name, quote=FALSE)
}
#--------------------[PTT Gate results]-----------------------
ref_word_csv(ptt_gate, "PTT-gate-word-fits.csv")


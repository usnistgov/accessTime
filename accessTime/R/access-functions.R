# This software was developed by employees of the National Institute of
# Standards and Technology (NIST), an agency of the Federal Government.
# Pursuant to title 17 United States Code Section 105, works of NIST
# employees are not subject to copyright protection in the United States and
# are considered to be in the public domain. Permission to freely use, copy,
# modify, and distribute this software and its documentation without fee is
# hereby granted, provided that this notice and disclaimer of warranty
# appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER
# EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY
# WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
# FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL
# CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR
# FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT
# LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING
# OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE,
# WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER
# OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND
# WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR
# USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.

#------------Access Fit Constructor and Validator----------------
accessFit <- function(fit,I0,curve_dat,session_dat,speaker_word){
  #' accessFit constructor
  #'
  #' Construct an access fit with model \code{fit}, asymptotic intelligibility
  #' \code{I0}, curve fitting data \code{curve_dat}, and session data
  #' \code{session_dat}.
  #' Returns an 'accessFit' object. Compatible with generic functions:
  #' \code{\link[base]{print}},
  #' \code{\link[stats]{coef}},
  #' \code{\link[stats]{confint}}.
  #'
  #'
  #' @param  fit \emph{nls.}
  #'               Logistic curve fit returned from
  #'               \code{\link[minpack.lm]{nlsLM}}.
  #'
  #' @param I0 \emph{numeric.}
  #'               Asymptotic intelligibility of the system under test.
  #'
  #' @param curve_dat \emph{data.frame.}
  #'               Data frame of the treated data sent to the curve fitting
  #'               function.
  #'
  #' @param session_dat \emph{list.}
  #'               List of raw data loaded from the session csv files.
  #'
  #' @param speaker_word \emph{character vector.}
  #'               Vector of speaker word pairs for data used in accessFit
  #'
  #' @return \emph{accessFit.}
  #'               Access fit object is a list based object containing the
  #'               elements input to the constructor. Has following structure:
  #'               \describe{
  #'                   \item{fit}{Fit object from \code{\link[minpack.lm]{nlsLM}}. Characterizes
  #'                   the intelligibility and access delay curves for the system under test.}
  #'                   \item{I0}{Asymptotic intelligibility for the system under test.}
  #'                   \item{curve_dat}{
  #'                       A data frame with the following 3 variables: \describe{
  #'                           \item{t}{PTT time, in seconds. Scaled such that 0 corresponds
  #'                           with the start of the word under test and positive time
  #'                           corresponds to the amount of time between PTT being pressed and
  #'                           the word being spoken.}
  #'                           \item{I}{Intelligibility}
  #'                           \item{speaker}{Speaker and word combination, e.g. 'F1 hook'}}
  #'                   }
  #'                   \item{session_dat}{
  #'                       A list of data frames with the following 8 variables: \describe{
  #'                           \item{PTT_time}{PTT time in audio clip time, in seconds.
  #'                           Corrected for audio interface latency.}
  #'                           \item{PTT_start}{PTT time in audio clip time, in seconds.
  #'                           Uncorrected for audio interface latency.}
  #'                           \item{ptt_st_dly}{PTT time interval, in seconds.}
  #'                           \item{P1_Int}{Intelligibility of P1.}
  #'                           \item{P2_Int}{Intelligibility of P2.}
  #'                           \item{m2e_latency}{Mouth-to-ear latency estimate for the given trial.}
  #'                           \item{underRun}{Number of detected buffer under runs}
  #'                           \item{overRun}{Number of detected buffer over runs}
  #'                           }
  #'                   }
  #'                   \item{speaker_word}{Array of the speaker word combos used for the access
  #'                   delay measurement.}
  #'     }
  #'
  #' @seealso \code{\link[minpack.lm]{nlsLM}}
  #'
  #' @export

  # Construct accessFit
  acF <- list(fit = fit,
              I0 = I0,
              curve_dat = curve_dat,
              session_dat = session_dat,
              speaker_word = speaker_word)

  class(acF) <- "accessFit"

  validate_accessFit(acF)


  return(acF)
}

validate_accessFit <- function(accessFit){
  stopifnot(exprs= {
    is.numeric(accessFit$I0) && length(accessFit$I0)==1
    is.data.frame(accessFit$curve_dat)
    is.list(accessFit$session_dat)
    all(sapply(accessFit$session_dat,is.data.frame))
    class(accessFit$fit) == "nls"
    all(sapply(accessFit$speaker_word,is.character))
  })
  return(TRUE)
}

#----------------Practical Access Fit Methods----------------------
read_accessData <- function(sessionFiles, cutDir,cutFiles=NULL){
  #'Read access delay csv files and associated audio cut point files
  #'
  #'Read the access delay csv files in \code{sessionFiles}, identify the audio
  #'clips used for the tests, and load in the associated cut point files from
  #'\code{cutDir}.
  #'
  #'@param sessionFiles \emph{character array.} Array of csv file names
  #'  associated with a particular access delay test.
  #'
  #'@param cutDir \emph{character array.} Path of the folder that contains the
  #'  cutpoint files for the audio clips used in the access delay test. Can also
  #'  pass in an array of directories.
  #'
  #'@param cutFiles \emph{character array.} Array of cutpoint file names. Note
  #'  that if \code{cutFiles} is not \code{NULL}, it will override whatever is
  #'  input for \code{cutDir}.
  #'
  #'@return \emph{List} with the following elements:
  #'
  #'@return \code{dat} \emph{list.} List of data frames containing the raw
  #'  access delay data of each csv file in \code{sessionFiles}.
  #'
  #'@return \code{cutPoints} \emph{list.} List of data frames containing the
  #'  cutpoints of the audio clips used in testing. Cutpoints describe the
  #'  samples at which P1 and P2 start and end in the audio clip.
  #'
  #'@return \code{fs} \emph{numeric.} Sampling rate of the audio clips used in
  #'  testing (Hz).
  #'
  #'@return \code{audio_clips} \emph{character array.} Array of audio clips
  #'  associated with each csv file in \code{sessionFiles}.
  #'
  #'@return \code{speaker_word} \emph{character array.} Array of the speaker and
  #'  word combination (e.g. 'F1 hook') for each audio clip.
  #'
  #' @examples
  #' # Path to included raw data
  #' raw_path <- system.file("extdata", "Measurements", package = "accessTime")
  #'
  #' # All included raw data tests
  #' raw_testNames <- list.files(raw_path)
  #'
  #' # Full path to each test
  #' raw_testPath <- file.path(raw_path,raw_testNames)
  #'
  #' # Session CSV Files for each raw test
  #' raw_sessionFiles <- lapply(raw_testPath,list.files)
  #'
  #' # Full path to all session files for each test
  #' sessionFiles <- mapply(function(x,y){file.path(x,y)},raw_testPath,raw_sessionFiles,SIMPLIFY = FALSE)
  #' names(sessionFiles) <- raw_testNames
  #'
  #' # Directory to audio clip wav files and cut points
  #' cutDir <- system.file("extdata", "Audio_Clips", package="accessTime")
  #'
  #' # Read session data
  #' session_dat <- lapply(sessionFiles,read_accessData,cutDir)
  #'
  #' # Fit session data
  #' fit_data <- lapply(session_dat,function(access_data){
  #'                           fit_accessData(dat = access_data$dat,
  #'                                          cutPoints = access_data$cutPoints,
  #'                                          speaker_word = access_data$speaker_word,
  #'                                          fs = access_data$fs)
  #'                           })
  #'
  #'@export

  # Read in data files
  datFiles_unOrdered <- lapply(sessionFiles,
                               read.csv,
                               skip = 3)
  # Read in header information from sessionFiles
  # # Includes audio file and sampling rate
  datFiles_headerInfo <- lapply(sessionFiles,
                                read.csv,
                                sep = "=",
                                nrows = 2,
                                header = F,
                                colClasses = c(rep("character",2)))

  # Parse audio file and sampling rate from header info
  dat_clip <- sapply(datFiles_headerInfo,
                     function(x){basename(x$V2[1])})
  dat_fs <- sapply(datFiles_headerInfo,
                   function(x){x$V2[2]})

  # Check that sampling rates are consistent
  if(length(unique(dat_fs)) > 1){
    stop("Inconsistent sampling rate among files")
  } else{
    fs <- strtoi(dat_fs[1])
  }

  # Find sorted order of speaker files
  sf <- sortSpeakers(dat_clip,ext=".wav")
  # Resort datFiles
  datFiles <- datFiles_unOrdered[sf$order]
  # browser()
  if(is.null(cutFiles)){
    # Define cutpoints csv file name based off of audio file name
    clip_csv <- gsub(".wav",".csv",dat_clip)


    # browser()
    if(length(cutDir)==1){
      # If only one cutdir provided repeat it
      cutDir_all <- rep(cutDir,length(sessionFiles))
    } else if(length(cutDir) != length(sessionFiles)){
      stop("Length of cut dir not equal to length of sessionFiles")
    } else{
      cutDir_all <- cutDir
    }

    # Define full path to cutpoints, in order of speaker order
    cutFiles <- file.path(cutDir_all[sf$order],clip_csv[sf$order])
  } else{
    # Reorder
    cutFiles <- cutFiles[sf$order]
  }

  # browser()
  # Load in cutpoints for audio files (samples that describe when P1 and P2 are played)
  cutPoints <- lapply(cutFiles,
                      read.csv
  )

  output <- list(dat = datFiles,
                 cutPoints = cutPoints,
                 fs = fs,
                 audio_clips = dat_clip[sf$order],
                 speaker_word = sf$speaker_word)
  return(output)
}

fit_accessData <- function(dat,cutPoints,speaker_word,fs){
  #' Treat and fit access delay data to a logistic curve
  #'
  #' Treat and fit access delay data to a logistic curve. First, recenters timing
  #' of access delay data so that the start of \code{P1} is at 0 seconds.
  #' Then, calculates the asymptotic intelligiblity of each word and fits a single
  #' logistic function across all of the access delay data. Returns an
  #' 'accessFit' object. Compatible with generic functions:
  #' \code{\link[base]{print}}, \code{\link[stats]{coef}},
  #' \code{\link[stats]{confint}}. See also
  #' \code{\link[accessTime]{read_accessData}} to read access delay data to be fit,
  #' and also \code{\link[accessTime]{process_accessData}} which is a wrapper
  #' function for both \code{read_accessData} and \code{fit_accessData}.
  #'
  #' @param dat \emph{list.}
  #'               List of data frames containing the access delay data for a
  #'               test. Data frame must have same variables as the csv files
  #'               output from an access delay measurement.
  #'
  #' @param cutPoints \emph{list.}
  #'               List of data frames containing the cutpoints of the audio clips
  #'               used in testing. Cutpoints describe the samples at which P1
  #'               and P2 start and end in the audio clip.
  #'
  #' @param speaker_word \emph{character array.}
  #'               Vector of speaKer and word combination for the words under test.
  #'               Example: 'F1 hook'
  #'
  #' @param fs \emph{numeric.}
  #'               Sampling rate of the audio clips used in testing (Hz).
  #'               Allows sample number to be converted to a time in seconds.
  #'
  #' @return \emph{accessFit.} object, a list containing the following
  #'               elements:
  #'
  #' @return \code{fit} \emph{nls.}
  #'               Logistic curve fit object returned from
  #'               \code{\link[minpack.lm]{nlsLM}}.
  #'
  #' @return \code{I0} \emph{numeric.}
  #'               Asymptotic intelligibility of the system under test.
  #'
  #' @return \code{curve_dat} \emph{data.frame.}
  #'               Data frame of the treated data sent to the curve fitting
  #'               function.
  #'
  #' @return \code{session_dat} \emph{list.}
  #'               List of raw data loaded from the session csv files. Same as
  #'               \code{dat}.
  #'
  #' @return \code{speaker_word} \emph{character array.}
  #'               Array of the speaker and word combination (e.g. 'F1 hook')
  #'               for each audio clip.
  #'
  #'
  #' @seealso \code{\link[minpack.lm]{nlsLM}}
  #'
  #' @examples
  #' # Path to included raw data
  #' raw_path <- system.file("extdata", "Measurements", package = "accessTime")
  #'
  #' # All included raw data tests
  #' raw_testNames <- list.files(raw_path)
  #'
  #' # Full path to each test
  #' raw_testPath <- file.path(raw_path,raw_testNames)
  #'
  #' # Session CSV Files for each raw test
  #' raw_sessionFiles <- lapply(raw_testPath,list.files)
  #'
  #' # Full path to all session files for each test
  #' sessionFiles <- mapply(function(x,y){file.path(x,y)},raw_testPath,raw_sessionFiles,SIMPLIFY = FALSE)
  #' names(sessionFiles) <- raw_testNames
  #'
  #' # Directory to audio clip wav files and cut points
  #' cutDir <- system.file("extdata", "Audio_Clips", package="accessTime")
  #'
  #' # Read session data
  #' session_dat <- lapply(sessionFiles,read_accessData,cutDir)
  #'
  #' # Fit session data
  #' fit_data <- lapply(session_dat,function(access_data){
  #'                           fit_accessData(dat = access_data$dat,
  #'                                          cutPoints = access_data$cutPoints,
  #'                                          speaker_word = access_data$speaker_word,
  #'                                          fs = access_data$fs)
  #'                           })
  #'
  #' @export

  # Define sample associated with word invariant time 0
  # # i.e. the sample where P1 starts becomes 0s in new time scale
  # browser()
  recenter_shift <- sapply(cutPoints,
                           function(x){x[1,"End"]/fs})

  # Extract PTT time and P1 intelligibility from data file
  fresh_dat <- lapply(dat,
                      function(x){x[,c("PTT_time","P1_Int")]})


  # Total number of tests
  nT <- length(fresh_dat)
  for(test in 1:nT){
    # For each test recenter push to talk time to be word invariant (0s represents start of P1)
    fresh_dat[[test]]$PTT_time <- recenter_shift[test] - fresh_dat[[test]]$PTT_time
    #
    fresh_dat[[test]]$Speaker <- speaker_word[test]
  }

  # Put all data into single data frame
  curve_dat <- do.call("rbind",fresh_dat)
  # Relabel columns of data
  colnames(curve_dat) <- c("t","I","speaker")

  # Calculate asymptotic intelligibility
  I0 <- mean(sapply(dat,function(x){mean(x$P2_Int)}))

  logist_fit <- tryCatch({
    # Try to fit linear curve to data to predict t0 and lambda

    # Find all indices that are minimum intelligibility
    min_vals <- which(curve_dat$I == min(curve_dat$I))
    # Find all indices that are maximum intelligibility
    max_vals <- which(curve_dat$I == max(curve_dat$I))

    #TODO: Could make this smarter later...but pretty effective for now
    # Fit line between mean minimum value and mean maximum value
    min_mean <- mean(curve_dat$t[min_vals])
    lin_start <- which.min(abs(min_mean-curve_dat$t[min_vals]))

    max_mean <- mean(curve_dat$t[max_vals])
    lin_end <- which.min(abs(max_mean - curve_dat$t[max_vals]))

    if(lin_start >= lin_end){
      stop("Unable to identify good starting region")
    }
    line_fit <- lm(curve_dat$I[lin_start:lin_end]~curve_dat$t[lin_start:lin_end])

    # Predict t0 to be midpoint between last min and first max
    t0 <- mean(curve_dat$t[c(lin_start,lin_end)])
    # Predict lambda to be -1/slope of linear model
    lambda = -1/line_fit$coefficients[2]
    names(lambda)<-NULL
    if(lambda > 0){
      stop("Unable to identify good starting region")
    }
    # Initialize start for parameters to be fit
    start <- list(t0=t0,
                  lambda=lambda)

    # Fit logistic function to data
    logist_fit <- minpack.lm::nlsLM(I~I0/(1 + exp((t-t0)/lambda)),
                                    data=curve_dat,
                                    start = start
    )
  }, error= function(e){

    warn_msg <- paste("Predictive initial parameter fit failed, using naive parameters for fit.")
    warning(warn_msg)

    # Initialize start for parameters to be fit (naive guesses)
    start <- list(t0 = 0, lambda=-0.1)

    # Fit logistic function to data
    logist_fit <- minpack.lm::nlsLM(I~I0/(1 + exp((t-t0)/lambda)),
                                    data=curve_dat,
                                    start = start
    )
    return(logist_fit)
  }
  )




  output <- accessFit(fit = logist_fit,
                      I0 = I0,
                      curve_dat = curve_dat,
                      session_dat = dat,
                      speaker_word = speaker_word)

  return(output)
}



process_accessData <- function(sessionFiles,cutDir, cutFiles = NULL){
  #' Wrapper function to read, process, and fit access delay data
  #'
  #' Read in access delay data, treat it, and fit a logistic function to the
  #' treated data. Relies on calls to \code{\link[accessTime]{read_accessData}}
  #' and \code{\link[accessTime]{fit_accessData}}. Returns an 'accessFit' object.
  #' Compatible with generic functions: \code{\link[base]{print}},
  #' \code{\link[stats]{coef}}, \code{\link[stats]{confint}}.
  #'
  #' @param sessionFiles \emph{character array.}
  #'               Array of csv file names associated with a particular access
  #'               delay test.
  #'
  #'@param cutDir \emph{character array.} Path of the folder that contains the
  #'  cutpoint files for the audio clips used in the access delay test. Can also
  #'  pass in an array of directories.
  #'
  #'@param cutFiles \emph{character array.} Array of cutpoint file names. Note
  #'  that if \code{cutFiles} is not \code{NULL}, it will override whatever is
  #'  input for \code{cutDir}.
  #'
  #' @return \emph{accessFit.}
  #'               Access fit object is a list containing the following
  #'               elements:
  #'
  #' @return \code{fit} \emph{nls.}
  #'               Logistic curve fit returned from
  #'               \code{\link[minpack.lm]{nlsLM}}.
  #'
  #' @return \code{I0} \emph{numeric.}
  #'               Asymptotic intelligibility of the system under test.
  #'
  #' @return \code{curve_dat} \emph{data.frame.}
  #'               Data frame of the treated data sent to the curve fitting
  #'               function.
  #'
  #' @return \code{session_dat} \emph{list.}
  #'               List of raw data loaded from the session csv files.
  #'
  #' @seealso \code{\link[minpack.lm]{nlsLM}}
  #' @examples
  #' # Path to included raw data
  #' raw_path <- system.file("extdata", "Measurements", package = "accessTime")
  #'
  #' # All included raw data tests
  #' raw_testNames <- list.files(raw_path)
  #'
  #' # Full path to each test
  #' raw_testPath <- file.path(raw_path,raw_testNames)
  #'
  #' # Session CSV Files for each raw test
  #' raw_sessionFiles <- lapply(raw_testPath,list.files)
  #'
  #' # Full path to all session files for each test
  #' sessionFiles <- mapply(function(x,y){file.path(x,y)},raw_testPath,raw_sessionFiles,SIMPLIFY = FALSE)
  #' names(sessionFiles) <- raw_testNames
  #'
  #' # Directory to audio clip wav files and cut points
  #' cutDir <- system.file("extdata", "Audio_Clips", package="accessTime")
  #'
  #' # Read, process, and fit session data
  #' fit_data <- lapply(sessionFiles,process_accessData,cutDir)
  #'
  #' @export

  # Read in access data
  # browser()
  if(!is.null(cutFiles)){
    access_data <- read_accessData(sessionFiles,cutDir="",cutFiles = cutFiles)
  } else{
    access_data <- read_accessData(sessionFiles,cutDir)

  }

  # Fit access data
  fit_data <- fit_accessData(dat = access_data$dat,
                             cutPoints = access_data$cutPoints,
                             speaker_word = access_data$speaker_word,
                             fs = access_data$fs)

  return(fit_data)
}
#-----------------Custom Access Fit Methods------------------

eval_access <- function(accFit,alpha,sys_dly_unc=0){
  #' Evaluate access times of accessFit object
  #'
  #' Evaluates an access delay function derived from an access fit object,
  #' \code{accFit}, at the values \code{alpha}.
  #'
  #' @param alpha \emph{numeric vector.}
  #'               Values between 0 and 1 that describe the fractional value of
  #'               the asymptotic intelligibility for an access delay
  #'               measurement.
  #'
  #' @param accFit \emph{accessFit.}
  #'               \code{\link[accessTime]{accessFit}} object
  #'
  #' @param sys_dly_unc Uncertainty of the measurement system delay.
  #'               Accounts for previous correction of PTT timing.
  #'
  #' @return \code{Values} \emph{data.frame.}
  #'               Data frame with three varaibles: alpha, access_time, and
  #'               uncertainty. Each observation describes the access delay
  #'               associated with an intelligibility of \code{alpha}*\code{I0}.
  #'               Note that access delay values are not dependent on I0.
  #'
  #'@examples
  #'# Evaluation of data collected for NISTIR XXXX
  #'
  #' # Define alpha vector
  #' alphas <- seq(from = 0.01, to = 0.99, by = 0.01)
  #'
  #' # Define system delay uncertainty
  #' sys_dly_unc <- 1e-3*0.07/1.96
  #'
  #' access_delays <- eval_access(ptt_gate,alphas,sys_dly_unc)
  #'
  #'@seealso \code{\link[accessTime]{accessFit}}
  #'
  #'@references Pieper J, Frey J, Greene C, Soetan Z, Thompson T, Bradshaw D,
  #' Voran S (2019) Mission Critical Voice QoE Access Time Measurement Methods.
  #' \emph{NISTIR}. URL \url{https://doi.org/10.6028/NIST.IR.XXXX}
  #'
  #'@export


  UseMethod("eval_access")
}

eval_access.accessFit <- function(accFit,alpha,sys_dly_unc=0){
  #' @method eval_access accessFit
  #' @export

  # Grab coefficients from curve fit

  coeffs <- coef(accFit)
  # Define acess time function as:
  # $ \tau_A(\alpha) = \lambda \cdot \ln(\frac{1-\alpha}{\alpha}) + t_0 $

  vals <- coeffs["lambda"] * log((1 - alpha)/alpha) + coeffs["t0"]

  # Grab covariance matrix of curve parameters
  Cov <- vcov(accFit$fit)

  # Define constant in \alpha
  C <- log((1-alpha)/alpha)

  # Define variance of estimate $\hat{t}$
  Var_t <- C^2 * Cov["lambda","lambda"] + Cov["t0","t0"] + 2 * C * Cov["lambda","t0"]

  # Get uncertainty of access time estimate
  unc <- sqrt(Var_t + sys_dly_unc^2)

  # Output list
  y<- data.frame(alpha=alpha,
                 access_time= vals,
                 uncertainty = unc)
  rownames(y) <- alpha
  return(y)
}

eval_intell <- function(accFit,t){
  #' Evaluate an intelligibility of accessFit object
  #'
  #' Evaluates an intelligibility function, I(t), defined by the accessFit
  #' object, accFit, at the times defined by t.
  #'
  #' @param accFit \emph{accessFit.}
  #'               \code{\link[accessTime]{accessFit}} object.
  #'
  #' @param t \emph{numeric vector.}
  #'               Times at which to evaluate the intelligibility curve
  #'
  #' @return \code{Values} \emph{data.frame.}
  #'               Data frame with two variables: \code{t} and \code{I}. Each
  #'               observation describes the intelligibility of the system under
  #'               test at time \code{t}.
  #'
  #' @examples
  #' #Evaluation of data collected for NISTIR XXXX
  #'
  #' # Define time vector
  #' times <- seq(from = -0.5, to = 2, by = 0.01)
  #'
  #' intelligibility_values <- eval_intell(ptt_gate,times)
  #'
  #' @references Pieper J, Frey J, Greene C, Soetan Z, Thompson T, Bradshaw D,
  #' Voran S (2019) Mission Critical Voice QoE Access Time Measurement Methods.
  #' \emph{NISTIR}. URL \url{https://doi.org/10.6028/NIST.IR.XXXX}
  #'
  #'@seealso \code{\link[accessTime]{accessFit}}
  #'
  #' @export
  UseMethod("eval_intell")
}

eval_intell.accessFit <- function(accFit,t){
  #' @method eval_intell accessFit
  #' @export

  # Grab coefficients from curve fit object
  coeffs <- coef(accFit)
  # Define as logistic function
  # $ I(t) = \frac{I_0}{1 + e^{(t-t_0)/\lambda}} $
  y <- coeffs["I0"]/(1 + exp((t - coeffs["t0"])/coeffs["lambda"]))
  if(!is.null(names(y))){
    names(y) <- NULL
  }
  return(data.frame(t=t,
                    I=y))
}

#--------------------Generic S3 Access Fit Methods---------------------
print.accessFit <- function(x,...){
  #' @export
  model <- x$fit$call$formula
  # browser()
  cat("Model:\n")
  print(model)

  coefs <- coef(x)

  cat(paste0("I0: ", coefs["I0"], "\n"))
  cat(paste0("lambda: ", coefs["lambda"], "\n"))
  cat(paste0("t0: ", coefs["t0"], "\n"))

}

coef.accessFit <- function(object,...){
  #' @export
  paramCoef <- coef(object$fit)
  output <- c("I0" = object$I0,
              paramCoef)
  return(output)
}

confint.accessFit <- function(object, parm=NULL, level=0.95,...){
  #' @export
  #'
  # TODO: Fix labelling bug if parm has only one of t0 or lambda (also possible that someone could use different model I guess...)
  # # The rbind at the end messes with the names. Gets set to paramInt. When confint gets passed a length one vector for parm seems to return a numeric vector
  # # Not sure I can assign a row name to a numeric vector...
  interval <- c(1,-1) * rep((1-level)/2,2) + c(0,1)
  if(is.null(parm)){
    paramInt <- confint(object$fit,level=level)
  } else{
    parmPass <- parm[parm!="I0"]
    if(length(parmPass) == 0){
      paramInt <- NULL
    } else{
      paramInt <- confint(object$fit,parm=parm,level=level)
    }
  }

  if(is.null(parm) | any(parm == "I0")){
    dat <- object$session_dat
    R <- 10000
    p2_resamples <- sapply(dat,
                           function(y){replicate(R, mean(sample(y$P2_Int,length(y$P2_Int),replace=TRUE)))}
    )

    I0_resamples <- rowMeans(p2_resamples)
    I0 <- quantile(I0_resamples,interval)
  } else{
    I0 <- NULL
  }
  output <- rbind(I0,paramInt)
  return(output)
}

#--------------Extra Functions-----------------

sortSpeakers <- function(sf,ext=".csv"){
  #' Sort session file names or audio clip names alphabetically by speaker,
  #' word pairs.
  #'
  #' Sort file names that end in format of '_Speaker_bXX_wXX_word.'
  #' alphabetically by speaker, word.
  #'
  #' @param sf \emph{character vector.}
  #'               Vector of strings of form '*_Speaker_bXX_wXX_word*'.
  #'               Examples:
  #'               \code{"capture_Analog_Direct_24-Apr-2019_14-39-14_F1_b39_w4_hook.csv"}
  #'               \code{"capture_Analog_Direct_23-Apr-2019_15-32-52_F3_b15_w5_west.csv"}
  #'               \code{"capture_Analog_Direct_23-Apr-2019_11-54-00_M3_b22_w3_cop.csv"}
  #'               \code{"capture_Analog_Direct_23-Apr-2019_08-12-08_M4_b18_w4_pay.csv"}
  #'
  #' @param ext \emph{character.}
  #'               File extension of the elements of \code{sf}.
  #'
  #' @return \emph{List} with following elements:
  #'
  #' @return \code{ordered} \emph{character vector.}
  #'               Alphabetized version of \code{sf}.
  #'
  #' @return \code{speaker_word} \emph{character vector.}
  #'               The speaker word combination extracted from \code{sf}.
  #'
  #' @return \code{order} \emph{numeric vector.}
  #'               Indices such that \code{ordered = sf[order]}.
  #'
  #
  bases <- basename(sf)
  noExt <- unlist(strsplit(bases,ext))
  byUnderScore <- strsplit(noExt,"_")

  N<- length(sf)
  # Preallocate arrays
  words <- vector("character",N)
  wIxs <- vector("character",N)
  bIxs <- vector("character",N)
  speakers <- vector("character",N)
  for(speaker in 1:N){
    # Length of split array
    Nsplit <- length(byUnderScore[[speaker]])
    # Word
    words[speaker] <- byUnderScore[[speaker]][Nsplit]
    # Word index (e.g. w1,w2,...,w6)
    wIxs[speaker] <- byUnderScore[[speaker]][Nsplit-1]
    # Batch index (e.g. b1,b2,...,b50)
    bIxs[speaker] <- byUnderScore[[speaker]][Nsplit-2]
    # Speaker name (e.g. F1,F3,M3,M4)
    speakers[speaker] <-byUnderScore[[speaker]][Nsplit-3]
  }

  sWord <- paste(speakers,words)

  sIx <- order(sWord)
  return(list(ordered=sf[sIx],
              speaker_word = sWord[sIx],
              order = sIx)
  )

}
#-------------Plotting Functions...----------------------
plot_wordIntCurves <- function(accFit,int_curve,title=""){
  #' Plot intelligibility curves for individual words
  #'
  #' Plot intelligibility curves for individual words associated with access
  #' delay measurement. Useful to see the contributions of each word towards
  #' final intelligibility curve results.
  #'
  #' @param accFit \emph{accessFit.}
  #'                \code{\link[accessTime]{accessFit}} object.
  #'
  #' @param int_curve \emph{data.frame.}
  #'                Data frame with following three variables:
  #'                \describe{
  #'                \item{t}{PTT time in seconds.
  #'                Corrected such that 0 s corresponds to the beginning of the
  #'                word under test.}
  #'                \item{I}{Intelligibility}
  #'                \item{speaker}{Speaker word pair, e.g. 'F1 hook`}}
  #'
  #'
  #' @param title \emph{Character.} Title for plot
  #'
  #' @return \emph{ggplot} object
  #'
  #' @import ggplot2
  #' @export
  #'
  #' @examples
  #' # Path to included raw data
  #' raw_path <- system.file("extdata", "Measurements", package = "accessTime")
  #'
  #' # All included raw data tests
  #' raw_testNames <- list.files(raw_path)
  #'
  #' # Full path to each test
  #' raw_testPath <- file.path(raw_path,raw_testNames)
  #'
  #' # Session CSV Files for each raw test
  #' raw_sessionFiles <- lapply(raw_testPath,list.files)
  #'
  #' # Full path to all session files for each test
  #' sessionFiles <- mapply(function(x,y){file.path(x,y)},raw_testPath,raw_sessionFiles,SIMPLIFY = FALSE)
  #' names(sessionFiles) <- raw_testNames
  #'
  #' # Directory to audio clip wav files and cut points
  #' cutDir <- system.file("extdata", "Audio_Clips", package="accessTime")
  #'
  #'  # Calculate accessFit objects for each technology
  #' all_dat <- lapply(sessionFiles,# Inputs
  #'      function(sesh){process_accessData(sesh,cutDir)})
  #'
  #' # Calculate accessFit objects for each individual word
  #' all_dat_indv <- lapply(sessionFiles, function(sesh){
  #'   lapply(sesh,function(word){
  #'    process_accessData(word,cutDir)
  #'  })
  #' })
  #'
  #' # Time Vector
  #' times <- seq(from=-0.5,to=2,by=0.01)
  #'
  #' # Calculate Intelligibility for each curve
  #' I_ts_indv <- lapply(all_dat_indv,
  #'                  function(tech){
  #'                      lapply(tech,function(word){
  #'                          eval_intell(word,times)
  #'                       })
  #'                   })
  #' for(tech in 1:length(I_ts_indv)){
  #'     # Name the words in the lists
  #'     names(I_ts_indv[[tech]]) <- sapply(all_dat_indv[[tech]],function(x){x$speaker_word})
  #'     for(word in 1:length(I_ts_indv[[tech]])){
  #'     # Assign speaker word combo to the data frames
  #'         I_ts_indv[[tech]][[word]]$speaker <- all_dat_indv[[tech]][[word]]$speaker_word
  #'     }
  #' }
  #' # Make one data frame for each technology
  #' intell_dat_words <- lapply(I_ts_indv,
  #'     function(x){do.call("rbind", x)})
  #'
  #' plotNames <- names(all_dat)
  #'
  #' # Make individual word pltos
  #' Int_plots_split<- mapply(plot_wordIntCurves,
  #'     all_dat,intell_dat_words,plotNames,
  #'     SIMPLIFY = FALSE)
  #'
  p <-  ggplot(accFit$curve_dat, aes(x = t, y = I)) +
    geom_point(aes(color=speaker,shape=speaker)) +
    # geom_line(data = int_curve, aes(x=int_times, y=cdat),  size = 1.3) +
    geom_line(data = int_curve, aes(x=t, y=I, color=speaker),  size = 1.3) +
    scale_colour_manual(values = c("#999999","#E69F00","#CC79A7", "#56B4E9"))+
    scale_shape_manual(values = c(17, 19, 0, 4)) +
    theme_minimal() +
    # guides(fill="none", color="none") +
    theme(legend.title = element_blank(), plot.title = element_text(hjust = 0.5)) +
    xlab("t [s]") + ylab("Intelligibility") + ggtitle(title) +
    scale_x_continuous(breaks = round(seq(-.6, 2, by = 0.2),1)) +
    scale_y_continuous(breaks = round(seq(0, 1, by = 0.1),1))
  return(p)
}

plot_techIntCurve <- function(accFit,int_curve,title=""){
  #' Plot intelligibility curve for a technology
  #'
  #' Plot intelligibility curve made up of multiple words across one technology.
  #'
  #' @param accFit \emph{accessFit.}
  #'                \code{\link[accessTime]{accessFit}} object.
  #'
  #' @param int_curve \emph{data.frame.}
  #'                Data frame of intelligibility values from
  #'                \code{\link[accessTime]{eval_intell}} function. Must contain two variables:
  #'                \describe{
  #'                    \item{t}{PTT time, in seconds. Time corrected for audio
  #'                    clips such that 0 seconds corresponds to PTT being
  #'                    pressed right at the beginning of the word being spoken.}
  #'                    \item{I}{Intelligibility}
  #'                 }
  #'
  #' @param title \emph{character.} Title of the plot
  #'
  #' @return \emph{ggplot}
  #'
  #' @examples
  #' # Times to evaluate intelligibility at
  #' times <- seq(from = -0.5, to = 2, by = 0.01)
  #'
  #' # Intelligibility as function of time
  #' intelligibility_values <- eval_intell(ptt_gate,times)
  #'
  #'
  #' plot_techIntCurve(ptt_gate,intelligibility_values,
  #'                   title="PTT Gate Intelligibility Curve")
  #' @import ggplot2
  #' @export
  p <-  ggplot(accFit$curve_dat, aes(x = t, y = I)) +
    geom_point(aes(fill="Data"), shape=20, size=1,alpha=1) +
    geom_line(data = int_curve, aes(x=t, y=I, color="Fitted Line"),  size = 1.5) +
    theme_minimal() +  guides(fill="none", color="none") +
    theme(legend.title = element_blank(), plot.title = element_text(hjust = 0.5)) +
    xlab("t [s]") + ylab("Intelligibility") + ggtitle(title) +
    scale_x_continuous(breaks = round(seq(-.6, 2, by = 0.2),1)) +
    scale_y_continuous(breaks = round(seq(0, 1, by = 0.1),1))
  return(p)
}

plot_accessCurve <- function(access_dat,title=""){
  #' Plot access delay curve
  #'
  #' Plot access delay curve values calculated from an accessFit object.
  #'
  #' @param access_dat \emph{data.frame}
  #'               Data frame with the following three variables:
  #'               \describe{
  #'               \item{alpha}{Value between 0 and 1. Describes a fraction of
  #'               the asymptotic intelligibility, I0, achieved.}
  #'               \item{access_time}{Access delay values, in seconds.}
  #'               \item{uncertainty}{Standard, unexpanded, uncertainty of access
  #'               delay values, in seconds.}}
  #'
  #' @param title \emph{character.}
  #'               Title of plot
  #'
  #' @return \emph{ggplot.}
  #'               ggplot object of plot.
  #'
  #'  @import ggplot2
  #' @export
  #'
  #' @examples
  #'
  #' # Define alpha vector
  #' alphas <- seq(from = 0.5, to = 0.99, by = 0.01)
  #'
  #' # Define system delay uncertainty
  #' sys_dly_unc <- 1e-3*0.07/1.96
  #'
  #' # Evaluate access delays
  #' access_delays <- eval_access(ptt_gate,alphas,sys_dly_unc)
  #'
  #' plot_accessCurve(access_delays,"PTT Gate Access Delay")
  #'


  q <-  ggplot(access_dat, aes(x = alpha, y = access_time)) +
    geom_line(size=1) +
    geom_line(aes(y=access_time+1.96*uncertainty, color="Upper Bound"), linetype="dashed",  size = .75) +
    geom_line(aes(y=access_time-1.96*uncertainty, color="Lower Bound"), linetype="dashed", size = .75) +
    theme_minimal() +
    theme(legend.title = element_blank(), plot.title = element_text(hjust = 0.5)) +
    ylab("Access Delay [s]") + xlab("Alpha") + ggtitle(title)
  return(q)
  # }
}

plot_compareAccessCurves <- function(access_df, title="",comp_type = "relative"){
  #' Compare access delay curves
  #'
  #' Compare access delay curves across technologies. Can compare in two ways:
  #' relative and flat comparisons. Relative comparisions use the percentage
  #' achieved of the baseline performance level for comparisions. This removes
  #' the maximum intelligibility of each technology from the comparision, and
  #' instead focuses on how long it takes each technology to reach its own
  #' maximum performance level. On the other hand flat comparisons compare
  #' access delays based on the actual intelligibility level achieved by each
  #' technology.
  #'
  #' @param access_df \emph{data.frame.}
  #'               Data frame with the following variables:
  #'               \describe{
  #'               \item{groups}{Technology for given test}
  #'               \item{I}{Raw intelligibility value}
  #'               \item{alpha}{Percentage of asymptotic intelligibility achieved}
  #'               \item{access_time}{Access delay, in seconds}
  #'               \item{uncertainty}{Standard, unexpanded, uncertainty, in seconds}
  #'               \item{CI_U}{Upper boundary for 95\% confidence interval}
  #'               \item{CI_L}{Lower boundary for 95\% confidence interval}
  #'               }
  #'
  #' @param title \emph{character.}
  #'               Title of the plot
  #'
  #' @param comp_type \emph{character.}
  #'               Comparison type, one of either "flat" or "relative".
  #'               Flat compares access delay as a function of raw
  #'               intelligibility. Relative compares access delay as a function
  #'                of the fraction of asymptotic intelligibility achieved for
  #'                each technology.
  #'
  #' @return \emph{ggplot.} Plot object
  #'
  #' @import ggplot2
  #' @export
  #' @examples
  #' if (requireNamespace("dplyr", quietly = TRUE)) {
  #' #  Make a list of all tests
  #' all_tests <- list("PTT Gate" = ptt_gate,
  #'                   "Analog Direct" = analog_direct,
  #'                   "Analog Conventional" = analog_conventional,
  #'                   "P25 Direct" = p25_direct,
  #'                   "P25 Trunked Phase 1" = p25_trunked_phase1,
  #'                   "P25 Trunked Phase 2" = p25_trunked_phase2)
  #'
  #' # Define alpha vector
  #' alphas <- seq(from = 0.5, to =0.99, by = 0.01)
  #'
  #' # Define system delay uncertainty
  #' sys_dly_unc <- 1e-3*0.07/1.96
  #'
  #' # Evaluate access delays for each test
  #' A_ts_alpha <- lapply(all_tests,
  #'      function(x){eval_access(x,alphas,sys_dly_unc)}
  #'      )
  #' # Grab Asymptotic Intelligibility for each technology
  #' I0s <- sapply(all_tests,coef)["I0",]
  #'
  #' # Add the raw intelligibility scores to data frame
  #' A_ts <- mapply(function(x,y){
  #'         raw_ints <- x$alpha*y
  #'         return(data.frame(I=raw_ints,x))
  #'     },
  #'     A_ts_alpha,I0s,
  #'     SIMPLIFY = FALSE)
  #'
  #' # Combine access delays into single data frame
  #' acc_df <- dplyr::bind_rows(A_ts,.id="groups")
  #'
  #' # Compute upper (U) and lower (L) bounds of 95% confidence interval
  #' acc_df$CI_U <- acc_df$access_time + 1.96*acc_df$uncertainty
  #' acc_df$CI_L <- acc_df$access_time - 1.96*acc_df$uncertainty
  #'
  #' #---------------Example 1: Relative Intelligibility Comparison-------------
  #' # -- This example compares the access delay as a function of alpha, or the
  #' # fraction of the asymptotic intelligibility achieved by each technology.
  #' # Here access delays for an alpha value of 0.8 corresponds to the time it
  #' # takes for technologies to reach 80% of their baseline performance. --
  #'
  #' plot_compareAccessCurves(acc_df,"Relative Access Delay Comparisions")
  #'
  #'
  #' #---------------Example 2: Flat Intelligibility Comparison-------------
  #' # -- This example directly compares the amount of time for each technology
  #' # to reach the same level of intelligibility, regardless of their asymptotic
  #' # intelligibility. It is important to note however that the access delay for
  #' # intelligibility values greater than the asymptotic intelligibility, I0, of
  #' # a technology will be infinite. --
  #'
  #' plot_compareAccessCurves(acc_df,"Flat Access Delay Comparisions",
  #'                          comp_type = "flat")
  #' }

  # The palette with black:
  cbbPalette <- c("#000000", "#E69F00", "#009E73", "#F0E442", "#0072B2", "#CC79A7","#56B4E9")

  if(comp_type == "flat"){
    combo_accPlot<-ggplot(acc_df,aes(x=alpha,y=access_time))+
      geom_line(aes(color=groups),size = 1)+
      geom_line(aes(y=CI_U,color=groups),linetype = "dashed",size=0.75) +
      geom_line(aes(y=CI_L,color=groups),linetype = "dashed",size=0.75) +
      theme_minimal()+
      theme(legend.title=element_blank(),
            text=element_text(size=20))+
      ylab("Access Time [s]") + xlab("Intelligibility") +
      # To use for line and point colors, add
      scale_colour_manual(values=cbbPalette) +
      ggtitle(title)
  } else if(comp_type == "relative"){
    combo_accPlot<-ggplot(acc_df,aes(x=I,y=access_time))+
      geom_line(aes(color=groups),size = 1)+
      geom_line(aes(y=CI_U,color=groups),linetype = "dashed",size=0.75) +
      geom_line(aes(y=CI_L,color=groups),linetype = "dashed",size=0.75) +
      theme_minimal()+
      theme(legend.title=element_blank(),
            text=element_text(size=20))+
      ylab("Access Time [s]") + xlab(expression(alpha)) +
      # To use for line and point colors, add
      scale_colour_manual(values=cbbPalette) +
      ggtitle(title)
  } else{
    stop("Incompatible comp_type")
  }
  return(combo_accPlot)
}

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
# FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY varTHAT THE DOCUMENTATION WILL
# CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR
# FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT
# LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING
# OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE,
# WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER
# OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND
# WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR
# USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.

#------------Access Fit Constructor and Validator-------------------------------
accessFit <- function(fit, I0, curve_dat, session_dat, speaker_word, test_type){
  #' accessFit constructor
  #'
  #' Construct an access fit with model \code{fit}, asymptotic intelligibility
  #' \code{I0}, curve fitting data \code{curve_dat}, and session data
  #' \code{session_dat}.
  #' Returns an 'accessFit' object. Compatible with generic functions:
  #' \code{\link[base]{print}},
  #' \code{\link[stats]{coef}},
  #' \code{\link[stats]{confint}}.
  #' \code{\link[stats]{vcov}}.
  #'
  #'
  #' @param fit \emph{nls.}
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
  #' @param test_type \emph{character.}
  #'               Type of access fit to return. Either correction fit (PTT),
  #'               system under test fit (SUT), or a legacy fit (LEG).
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
  #'                   \item{test_type}{String reflecting the type of access fit.}
  #'     }
  #'
  #' @seealso \code{\link[minpack.lm]{nlsLM}}
  #' @references
  #' @export

  stopifnot(is.character(test_type))
  # Make sure test type is valid (case insensitive)
  if(test_type == "sut" | test_type == "SUT"){
    store_type <- "SUT"
    test_type <- "SUT"
    not_type <- "PTT"
  } else if(test_type == "ptt" | test_type == "PTT"){
    store_type <- "PTT"
    test_type <- "PTT"
    not_type <- "SUT"
  } else if(test_type == "leg" | test_type == "LEG"){
    store_type <- "LEG"
    test_type <- "SUT"
    not_type <- "PTT"
  } else{
    stop("Invalid test_type, must be SUT, PTT or LEG.  Not: ", test_type)
  }

  # create lists to hold the new structure
  # growing a list is bad, but I can optimize later,
  # besides, it'll be a max of 4 words, so not too bad
  aggr_curve_dat <- list()
  aggr_session_dat <- list()

  # name session dat for easier iterating
  names(session_dat) <- speaker_word

  # probably a better way to do this than for loops
  for (sw in speaker_word) {
    aggr_curve_dat[[sw]][[test_type]] <- curve_dat
    aggr_curve_dat[[sw]][[not_type]] <- NA
    aggr_session_dat[[sw]][[test_type]] <- session_dat[[sw]]
    aggr_session_dat[[sw]][[not_type]] <- NA
  }

  # Check

  # Construct accessFit
  acF <- list(
    fit=fit,
    I0=I0,
    curve_dat=aggr_curve_dat,
    session_dat=aggr_session_dat,
    speaker_word=speaker_word,
    test_type=store_type
  )

  class(acF) <- "accessFit"

  validate_accessFit(acF)

  return(acF)
}

validate_accessFit <- function(accFit){
  stopifnot(exprs= {
    is.numeric(accFit$I0) && length(accFit$I0)==1
    is.list(accFit$curve_dat)
    is.list(accFit$session_dat)
    all(sapply(accFit$session_dat,is.list))
    all(sapply(accFit$speaker_word,is.character))
    is.character(accFit$test_type)
  })
  # ---SUT/PTT Features---------
  if(accFit$test_type == "SUT" | accFit$test_type == "PTT"){
    class(accFit$fit) == "nls"
    if(accFit$test_type == "SUT"){
      test_type <- "SUT"
      not_type <- "PTT"
    } else{
      test_type <- "PTT"
      not_type <- "SUT"
    }
    # Check that
    if(length(accFit$curve_dat) > 1 | length(accFit$session_dat) > 1){
      stop("Invalid accessFit, SUT or PTT with multiple sessions")
    } else{
      stopifnot(exprs={
        # Check that curve data is properly structured
        class(accFit$curve_dat[[1]][[test_type]]) == "data.frame"
        all(names((accFit$curve_dat[[1]][[test_type]])) == c("t", "I", "speaker"))
        # Don't have not type, with right format
        not_type %in% names(accFit$curve_dat[[1]])
        is.na(accFit$curve_dat[[1]][[not_type]])
        # Check that session data is properly structured
        class(accFit$session_dat[[1]][[test_type]]) == "data.frame"
        not_type %in% names(accFit$session_dat[[1]])
        is.na(accFit$session_dat[[1]][[not_type]])
      })
    }
  }else if(accFit$test_type == "COR"){
    #-------------COR Features----------------
    stopifnot(exprs={
      class(accFit$fit) == "aggregate_nls"
      # Do the lists match in length, names, and order?
      all(names(accFit[["curve_dat"]]) == names(accFit[["session_dat"]]))
      # Is there a PTT and SUT test for each word?
      all(sapply(accFit$curve_dat,function(x){all(names(x) == c("SUT", "PTT") | names(x) == c("PTT", "SUT"))}))
      all(sapply(accFit$session_dat,function(x){all(names(x) == c("SUT", "PTT") | names(x) == c("PTT", "SUT"))}))
      # Check structure of each word
      all(sapply(accFit$curve_dat,
                 function(x){
                   stopifnot(exprs={
                     "PTT" %in% names(x)
                     "SUT" %in% names(x)
                     class(x[["PTT"]]) == "data.frame"
                     all(names(x[["PTT"]]) == c("t","I","speaker"))

                     class(x[["SUT"]]) == "data.frame"
                     all(names(x[["SUT"]]) == c("t","I","speaker"))
                   })
                   return(TRUE)
                 })
      )
      all(sapply(accFit$session_dat,
                 function(x){
                   stopifnot(exprs={
                     "PTT" %in% names(x)
                     "SUT" %in% names(x)
                     class(x[["PTT"]]) == "data.frame"
                     class(x[["SUT"]]) == "data.frame"
                   })
                   return(TRUE)
                 })
      )
    })
  } else if(accFit$test_type == "LEG"){
    #-------------LEG Features----------------
    stopifnot(exprs = {
      class(accFit$fit) == "nls"
      all(names(accFit[["curve_dat"]]) == names(accFit[["session_dat"]]))
      # Is there a PTT and SUT test for each word?
      all(sapply(accFit$curve_dat,function(x){all(names(x) == c("SUT", "PTT") || names(x) == c("PTT", "SUT"))}))
      all(sapply(accFit$session_dat,function(x){all(names(x) == c("SUT", "PTT") || names(x) == c("PTT", "SUT"))}))
      # Check structure of each word

      all(sapply(accFit$curve_dat,
                 function(x){
                   stopifnot(exprs={
                     "PTT" %in% names(x)
                     "SUT" %in% names(x)
                     is.na(x[["PTT"]])

                     class(x[["SUT"]]) == "data.frame"
                     all(names(x[["SUT"]]) == c("t", "I", "speaker"))
                   })
                   return(TRUE)
                 })
      )
      all(sapply(accFit$session_dat,
                 function(x){
                   stopifnot(exprs={
                     "PTT" %in% names(x)
                     "SUT" %in% names(x)
                     is.na(x[["PTT"]])
                     class(x[["SUT"]]) == "data.frame"
                   })
                   return(TRUE)
                 })
      )
    })
  } else{
    stop(
      "Invalid test type, must be SUT, PTT, COR, or LEG, not: ",
      accessFit$test_type
      )
  }

  return(TRUE)
}

#--------------Aggregate Fit Constructor----------------------------------------
aggregate_nls <- function(sfits, pfits, sut_I0s){
  #' Aggregated access Fit constructor
  #'
  #' Construct an aggregated curve fit given SUT fits \code{sfits}, PTT fits
  #' \code{pfits}, and the asymptotic intelligibilities of the SUT fits \code{sut_I0s}
  #'
  #' Returns an 'aggregate_nls' object compatible with
  #' \code{\link[base]{print}},
  #' \code{\link[stats]{coef}},
  #' \code{\link[stats]{confint}},
  #' \code{\link[stats]{vcov}}
  #'
  #' @param sfits \emph{nls.}
  #'               Logistic curve fit returned from
  #'               \code{\link[minpack.lm]{nlsLM}}.
  #'
  #' @param pfits \emph{numeric.}
  #'               Data frame of the treated data sent to the curve fitting
  #'               function.
  #'
  #' @param sut_I0s \emph{data.frame.}
  #'               Asymptotic intelligibility of the system under test.
  #'
  #'
  #' @return \emph{aggregate_nls.}
  #'               Aggregate nls object provides aggregated fit parameters.
  #'               Has following structure:
  #'               \describe{
  #'                   \item{call}{Fit formula.}
  #'                   \item{lambda}{Linear combination of constituant lambda parameters.}
  #'                   \item{t0}{Linear combination of constituant t0 parameters.}
  #'                   \item{covar}{Propogated covariance matrix}
  #'                   \item{words}{List of words in constituant fits.}
  #'                   \item{orig_params}{List of SUT and PTT fit parameters.}
  #'                   \item{SUT_I0s}{Asymptotic intelligibilities associated with SUT fits.}
  #'     }
  #'
  #' @export


  # sfits and pfits should be the actual nls class object called "fit" in
  # an accessFit object (ugh terrible nomenclature).

  # Extract one formula
  formula <- sfits[[1]]$call$formula

  # Verify that all the fits share the same formula
  valid_sfits_formula <- sapply(sfits,function(x){x$call$formula == formula})
  valid_pfits_formula <- sapply(pfits,function(x){x$call$formula == formula})

  common_formula <- all(c(valid_sfits_formula, valid_pfits_formula))

  # Stop if formula not common to all fit objects
  if(!common_formula){
    stop(paste("Formula", formula, "not shared by all fit objects"))
  }

  # Extract coefficients from fits
  s_coef <- sapply(sfits, coef)
  p_coef <- sapply(pfits, coef)

  # Grab t0 values
  s_t0s <- s_coef["t0",]
  p_t0s <- p_coef["t0",]

  # Calculate aggregate t0
  t0 <- sum(s_t0s - p_t0s)/length(s_t0s)

  # Grab lambda values
  s_lambdas <- s_coef["lambda",]
  p_lambdas <- p_coef["lambda",]

  # Calculate aggregate lambda
  lambda <- sum(s_lambdas - p_lambdas)/length(s_lambdas)

  # Calculate variances
  s_vars <- lapply(sfits, vcov)
  p_vars <- lapply(pfits, vcov)

  covar <- Reduce('+', (c(s_vars, p_vars))) / length(s_lambdas)

  # perserve words for printing
  words <- names(sfits)

  agf <- list(
    call=list(formula=formula),
    lambda=lambda,
    t0=t0,
    covar=covar,
    words=words,
    orig_params=list(PTT=p_coef, SUT=s_coef),
    SUT_I0s=sut_I0s
  )

  # assign aggregate fit class (aggregate_nls)
  class(agf) <- "aggregate_nls"

  # Validate
  validate_aggregate_nls(agf)

  return(agf)
}

validate_aggregate_nls <- function(agf){
  stopifnot(
    exprs= {
      is.numeric(agf$t0) && is.numeric(agf$lambda)
      length(agf$covar) == 4
      is.double(agf$covar)
      all(sapply(agf$call$formula, is.language))
    }
  )
}

print.aggregate_nls <- function(x, ...){
  #' @export
  cat("Aggregate of multiple nonlinear regression models\n")
  model <- x$call$formula
  cat("Model:\n")
  print(model)

  coefs <- coef(x)

  cat(paste0("lambda: ", coefs["lambda"], "\n"))
  cat(paste0("t0: ", coefs["t0"], "\n"))

  cat(paste("Words fit:", paste0(x$words, collapse = ", "), "\n"))
}

confint.aggregate_nls <- function(object, parm=NULL, level=0.95, ...){
  #' @export
  # define quantile interval
  interval <- c(1,-1) * rep((1-level)/2, 2) + c(0, 1)

  # get coverage factor, k
  K <- qnorm(interval[2])

  # get params to confint on
  if(is.null(parm)){
    paramInt <- t(data.frame(
      't0'=K*c(-1, 1)*sqrt(object$covar['t0', 't0']) + object$t0,
      'lambda'=K*c(-1, 1)*sqrt(object$covar['lambda', 'lambda']) + object$lambda
    ))
    colnames(paramInt) <- interval
  } else{
    paramInt <- data.frame(sapply(parm, function(y) K*c(-1, 1)*sqrt(object$covar[y, y]) + object[[y]]))
    colnames(paramInt) <- parm
    rownames(paramInt) <- interval
    paramInt <- t(paramInt)
  }

  # combine calculated values into clean output
  output <- rbind(paramInt)
  return(output)
}

coef.aggregate_nls <- function(object, ...){
  #' @export
  (c(t0=object$t0, lambda=object$lambda))
}

vcov.aggregate_nls <- function(object, ...){
  #' @export
  object$covar
}

#----------------techFit alternative constructor--------------------------------

#TODO: Make a wrapper function that takes in sut files & cutpoints, ptt files &
#cutpoints, makes all individual fits, passes to techFit, returns a list with
#techFit and individual fits

techFit <- function(sut_fits, ptt_fits){
  #' Technology access Fit constructor
  #'
  #' Construct a technology fit given SUT curve fits \code{sut_fits}, and PTT
  #' curve fits \code{ptt_fits}
  #' Returns an 'accessFit' object. Compatible with generic functions:
  #' \code{\link[base]{print}},
  #' \code{\link[stats]{coef}},
  #' \code{\link[stats]{confint}},
  #' \code{\link[stats]{vcov}}.
  #'
  #'
  #' @param sut_fits \emph{accessFit.}
  #'               List of accessFit objects representing the WUTs through a respective SUT.
  #'
  #' @param ptt_fits \emph{accessFit.}
  #'               List of accessFit objects representing the WUTs through a PTT gate.
  #'
  #'
  #' @return \emph{accessFit.}
  #'               Technology fit object is a list based object containing the
  #'               elements input to the constructor. Has following structure:
  #'               \describe{
  #'                   \item{fit}{An aggregate_nls fit of the constituant fits.}
  #'                   \item{I0}{Arithmetic mean of asymptotic intelligibilites of the SUT fits.}
  #'                   \item{speaker_word}{List of keywords used in the SUT trial.}
  #'                   \item{test_type}{Test type. Set to "COR". Using this constructor implies a corrected fit.}
  #'     }
  #'
  #'
  #' @export
  #' @examples
  #' dat_path <- system.file("extdata", package="accessTime")
  #'  ptt_fits <- process_session_data(
  #'    "capture_PTT-gate_14-May-2021_07-30-20",
  #'    test_type = "PTT",
  #'    dat_path = dat_path
  #'    )
  #'
  #'  # Get SUT fits
  #'  sut_fits <- process_session_data(
  #'    "capture_LTE_14-Apr-2021_16-11-22",
  #'    test_type="SUT",
  #'    dat_path = dat_path
  #'  )
  #'
  #'  # Get technology fit
  #'  lte <- techFit(
  #'    sut_fits = sut_fits,
  #'    ptt_fits = ptt_fits
  #'  )

  # Grab words
  sut_words <- sapply(sut_fits, function(x) x[["speaker_word"]])
  ptt_words <- sapply(ptt_fits, function(x) x[["speaker_word"]])

  # Throw error if words are different
  stopifnot(sut_words == ptt_words)

  # Create aggregate fit to store in the techFit object
  sfits <- lapply(sut_fits, function(x){x$fit})
  pfits <- lapply(ptt_fits, function(x){x$fit})

  # Extract I0s from SUT data
  orig_I0 <- sapply(sut_fits, function(x) x$I0)

  fit <- aggregate_nls(sfits,pfits, orig_I0)

  tcf <- list(
    fit=fit,
    I0=mean(orig_I0),
    speaker_word=sut_words
  )

  # transfer data into the techFit structure
  for (ii in seq(length(sut_words))){
    for (dat in c("curve_dat", "session_dat")) {
      tcf[[dat]][[sut_words[[ii]]]][["SUT"]] <- sut_fits[[ii]][[dat]][[sut_words[[ii]]]][["SUT"]]
      tcf[[dat]][[sut_words[[ii]]]][["PTT"]] <- ptt_fits[[ii]][[dat]][[sut_words[[ii]]]][["PTT"]]
    }
  }

  tcf[["test_type"]] <- "COR"

  # Bestow classhood upon ye!
  class(tcf) <- "accessFit"

  # Validate integrity of the new class
  validate_accessFit(tcf)

  # Hand the instance back to the world for proper use
  return(tcf)
}

#----------------Practical Access Fit Methods-----------------------------------
read_accessData <- function(sessionFiles, cutFiles){
  #'Read access delay csv files and associated audio cut point files
  #'
  #'Read the access delay csv files in \code{sessionFiles}, identify the audio
  #'clips used for the tests, and load in the associated cut point files from
  #'\code{cutDir}.
  #'
  #'@param sessionFiles \emph{character array.} Array of csv file names
  #'  associated with a particular access delay test.
  #'
  #'@param cutFiles \emph{character array.} Array of cutpoint file names.
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
  #'@examples
  #'
  #' # Path to included raw data
  #' dat_path <- system.file("extdata", package="accessTime")
  #'
  #' # Analog Direct csv files
  #' data_files <- find_session_csv(
  #'   "capture_Analog_12-Nov-2020_08-26-11",
  #'   dat_path
  #'   )
  #'
  #' # Get the session and cut file for one WUT
  #' sessionFile <- data_files$sessions[1]
  #' cutFile <- data_files$cut[1]
  #' # Read session data
  #' sess_dat <- read_accessData(sessionFile, cutFile)
  #'
  #' # Fit session data
  #' fit_dat <- fit_accessData(
  #'   dat=sess_dat$dat,
  #'   test_type="SUT",
  #'   cutPoints=sess_dat$cutPoints,
  #'   speaker_word=sess_dat$speaker_word,
  #'   fs=sess_dat$fs
  #'   )
  #'
  #'@export

  # Read in data files
  datFiles_unOrdered <- lapply(
    sessionFiles,
    read.csv,
    skip=3
    )
  # Read in header information from sessionFiles
  # # Includes audio file and sampling rate
  datFiles_headerInfo <- lapply(
    sessionFiles,
    read.csv,
    sep="=",
    nrows=2,
    header=F,
    colClasses=c(rep("character", 2))
    )

  # Parse audio file and sampling rate from header info
  dat_clip <- sapply(
    datFiles_headerInfo,
    function(x){basename(x$V2[1])}
    )
  dat_fs <- sapply(
    datFiles_headerInfo,
    function(x){x$V2[2]}
    )

  # Check that sampling rates are consistent
  if(length(unique(dat_fs)) > 1){
    stop("Inconsistent sampling rate among files")
  } else{
    fs <- strtoi(dat_fs[1])
  }

  # Find sorted order of speaker files
  sf <- sortSpeakers(dat_clip, ext=".wav")
  # Resort datFiles
  datFiles <- datFiles_unOrdered[sf$order]

  # Reorder
  cutFiles <- cutFiles[sf$order]

  # Load in cutpoints for audio files (samples that describe when P1 and P2 are played)
  cutPoints <- lapply(
    cutFiles,
    read.csv
  )

  output <- list(
    dat=datFiles,
    cutPoints=cutPoints,
    fs=fs,
    audio_clips=dat_clip[sf$order],
    speaker_word=sf$speaker_word
    )

  return(output)
}

fit_accessData <- function(dat, test_type, cutPoints, speaker_word, fs, maxiter=50){
  #' Treat and fit access delay data to a logistic curve
  #'
  #' Treat and fit access delay data to a logistic curve. First, recenters timing
  #' of access delay data so that the start of \code{P1} is at 0 seconds.
  #' Then, calculates the asymptotic intelligiblity of each word and fits a single
  #' logistic function across all of the access delay data. Returns an
  #' \code{\link[accessTime]{accessFit}} object. Compatible with generic functions:
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
  #' @param test_type \emph{list.}
  #'               String indicating the type of test accociated with the fit.
  #'               I.e 'SUT', 'PTT', etc.
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
  #' @param maxiter \emph{numeric.}
  #'               Maximum number of iterations passed to fitting algorithm. Defaults to 50
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
  #' @return \code{test_type} \emph{character array.}
  #'               String reflecting the type of access fit.
  #'
  #' @seealso \code{\link[minpack.lm]{nlsLM}}
  #'
  #' @examples
  #' # Path to included raw data
  #' dat_path <- system.file("extdata", package="accessTime")
  #'
  #' # Analog Direct csv files
  #' data_files <- find_session_csv(
  #'   "capture_Analog_12-Nov-2020_08-26-11",
  #'   dat_path
  #'   )
  #'
  #' # Get the session and cut file for one WUT
  #' sessionFile <- data_files$sessions[1]
  #' cutFile <- data_files$cut[1]
  #'
  #' # Read session data
  #' sess_dat <- read_accessData(sessionFile, cutFile)
  #'
  #' # Fit session data
  #' fit_dat <- fit_accessData(
  #'   dat=sess_dat$dat,
  #'   test_type="SUT",
  #'   cutPoints=sess_dat$cutPoints,
  #'   speaker_word=sess_dat$speaker_word,
  #'   fs=sess_dat$fs
  #'   )
  #'
  #' @import minpack.lm
  #' @export

  # Define sample associated with word invariant time 0
  # # i.e. the sample where P1 starts becomes 0s in new time scale
  recenter_shift <- sapply(
    cutPoints,
    function(x){x[1,"End"]/fs}
    )

  # Extract PTT time and P1 intelligibility from data file
  fresh_dat <- lapply(
    dat,
    function(x){x[,c("PTT_time","P1_Int")]}
    )

  # Total number of tests
  nT <- length(fresh_dat)
  for(test in 1:nT){
    # For each test recenter push to talk time to be word invariant (0s represents start of P1)
    fresh_dat[[test]]$PTT_time <- recenter_shift[test] - fresh_dat[[test]]$PTT_time
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

    # Find average time that corresponds to minimum intelligibility
    min_mean <- mean(curve_dat$t[min_vals])
    # Measure distance in time between minimum intelligibility points from average
    lin_start_min <- which.min(abs(min_mean-curve_dat$t[min_vals]))
    # Find corresponding point in original data
    lin_start <- which(curve_dat$t == curve_dat$t[min_vals][lin_start_min])
    if(length(lin_start)>1){
      lin_start <- lin_start[1]
    }

    # Find average tiem that correspodns with maximum intelligibility
    max_mean <- mean(curve_dat$t[max_vals])
    # Measure distance in time between max intell points from average
    lin_start_max <- which.min(abs(max_mean - curve_dat$t[max_vals]))
    # Find corresponding point in original data
    lin_end <- which(curve_dat$t == curve_dat$t[max_vals][lin_start_max])
    if(length(lin_end) > 1){
      lin_end <- lin_end[length(lin_end)]
    }

    if(lin_start >= lin_end){
      stop("Unable to identify good starting region")
    }
    line_fit <- lm(curve_dat$I[lin_start:lin_end]~curve_dat$t[lin_start:lin_end])

    # Predict t0 to be midpoint between last min and first max
    t0 <- mean(curve_dat$t[c(lin_start, lin_end)])

    # Predict lambda to be -1/slope of linear model
    lambda = -1/(4*line_fit$coefficients[2])
    names(lambda) <- NULL
    if(lambda >=0){
      stop("Unable to identify good lambda initial value")
    }

    # Initialize start for parameters to be fit
    start <- list(
      t0=t0,
      lambda=lambda
      )

    # Fit logistic function to data
    logist_fit <- nlsLM(
      I~I0/(1 + exp((t-t0)/lambda)),
      data=curve_dat,
      start=start,
      control=nls.lm.control(maxiter=maxiter)
    )
  }, error=function(e){

    warn_msg <- paste("Predictive initial parameter fit failed, using naive parameters for fit.", e)
    warning(warn_msg)

    # Initialize start for parameters to be fit (naive guesses)
    start <- list(t0=0, lambda=-0.1)

    # Fit logistic function to data
    logist_fit <- nlsLM(
      I~I0/(1 + exp((t-t0)/lambda)),
      data=curve_dat,
      start=start
    )
    return(logist_fit)
  }
  )

  output <- accessFit(
    fit=logist_fit,
    I0=I0,
    curve_dat=curve_dat,
    session_dat=dat,
    speaker_word=speaker_word,
    test_type=test_type
    )

  return(output)
}

process_accessData <- function(sessionFiles, cutFiles, test_type, maxiter=50){
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
  #' @param cutFiles \emph{character array.}
  #'               Array of cutpoint file names.
  #'
  #' @param test_type \emph{character array.}
  #'               Indicates type of the test for the access fit.
  #'
  #' @param maxiter \emph{numeric.}
  #'               Maximum number of iterations passed to fitting algorithm. Defaults to 50
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
  #' @return \code{test_type} \emph{character array.}
  #'               String reflecting the type of access fit.
  #'
  #' @seealso \code{\link[minpack.lm]{nlsLM}}
  #' @examples
  #' # Path to included data
  #' data_path <- system.file("extdata", package="accessTime")
  #'
  #' # Get csvs based on identifier. Using Analog Direct
  #' data_files <- find_session_csv(
  #'  "capture_Analog_12-Nov-2020_08-26-11",
  #'  dat_path = data_path
  #'  )
  #'# Process fit for single WUT
  #' processed_data <- process_accessData(
  #'  data_files$sessions[1],
  #'  data_files$cut[1],
  #'  test_type="SUT",
  #'  maxiter=50
  #'  )
  #'
  #' @export

  # Read in access data
  access_data <- read_accessData(sessionFiles, cutFiles)

  # Fit access data
  fit_data <- fit_accessData(
    dat=access_data$dat,
    test_type=test_type,
    cutPoints=access_data$cutPoints,
    speaker_word=access_data$speaker_word,
    fs=access_data$fs,
    maxiter=maxiter
    )

  return(fit_data)
}

#-----------------Correction Convenience Loading Functions----------------------
find_session_csv <- function(id_str, dat_path="data", find_all=TRUE){
  #' Find all required csv files to process data based off of identifying string
  #'
  #' Find both the session and cutpoint files required for processing access
  #' delay data.
  #'
  #' This function relies on data in \code{dat_path} being stored in
  #' accordance with how MCV QoE measurement data structures. In particular
  #' \code{dat_path} must have folders \emph{csv} and \emph{wav}.
  #'
  #' \emph{csv}
  #' contains csv files for each test with all output measurement data. All
  #' measurement files are of the form
  #' \code{capture_\{Description\}_DD-Mon-YYYY_HH-MM-SS_\{Audio File\}.csv}
  #'
  #' \emph{wav} contains wav folders for each test, and are of the name
  #' \code{capture_\{Description\}_DD-Mon-YYYY_HH-MM-SS}. It is critical this
  #' folder contains the cutpoints for the transmit audio for an access delay test.
  #'
  #'
  #' @param id_str \emph{character array.}
  #'               Identifying character string for the tests, of the form
  #'               \code{capture_\{Description\}_DD-Mon-YYYY_HH-MM-SS}, which will
  #'               match both measurement data and the corresponding wav folder.
  #'
  #' @param dat_path \emph{character array.}
  #'               Parent directory containg measurement data csv and wav folders.
  #'
  #' @param find_all \emph{logical.}
  #'               Indicates type of the test for the access fit.
  #' @return List containing the following elements
  #'
  #' @return \code{sessions} \emph{character.}
  #'         Path using \code{dat_path} to all session csv files matching id_str.
  #'
  #' @return \code{cut} \emph{character.}
  #'         Path using \code{dat_path} to all cut point files matching id_str.
  #'
  #' @examples
  #' dat_path <- system.file("extdata", package="accessTime")
  #' # Identifying string for P25 Phase1 Trunked data
  #' id_str <- "capture_P25-Phase1-Trunked_04-Nov-2020_07-21-19"
  #'
  #' # Find data and cutpoint csv files
  #' sesh_csv <- find_session_csv(id_str,dat_path)
  #'
  #' # Generate SUT access fits for each word under test (WUT)
  #' p25p2_wut <- mapply(process_accessData,sesh_csv$sessions,sesh_csv$cut,"SUT",SIMPLIFY = FALSE)
  #' @import stringr
  #' @export

  # Function to find session csv in data directory and find cut file

  if(!dir.exists(dat_path)){
    stop(
      "Invalid dat_path, does not exist: ",
      normalizePath(dat_path)
      )
  }
  csv_path <- file.path(dat_path, "csv")

  if(!dir.exists(csv_path)){
    stop(
      "Invalid dat_path, csv folder does not exist within it: ",
      normalizePath(dat_path)
      )
  }
  csv_list <- list.files(csv_path)

  if(find_all){
    # Ensure searchign with most generic session string
    search_str <- "(capture_.+_\\d{2}-\\d{2}-\\d{2})"
    gen_ids <- str_extract(id_str, search_str)
    matches <- grepl(gen_ids, csv_list)
  } else{
    # Find matches in csv list
    matches <- grepl(id_str, csv_list)
  }

  session_csvs <- csv_list[matches]

  # remove csvs that are BAD
  has_bad <- grepl("\\d{2}-\\d{2}-\\d{2}_BAD", session_csvs)
  session_csvs <- session_csvs[!has_bad]

  # remove csvs that are temp
  has_temp <- grepl("\\d{2}-\\d{2}-\\d{2}_temp", session_csvs)
  session_csvs <- session_csvs[!has_temp]
  session_paths <- file.path(dat_path, "csv", session_csvs)

  # Extract audio from session file names
  ext_pattern <- "\\w\\d_b\\d{1,2}_w\\d_\\w+?(?=.csv)"
  audio_names <- str_extract(session_csvs, ext_pattern)

  # Define cutpoint names
  cut_names <- paste0("Tx_",audio_names,".csv")
  cut_paths <- file.path(dat_path, "wav", id_str, cut_names)

  return(list(sessions=session_paths,
              cut=cut_paths))
}

process_session_data <- function(id_strs, test_type, dat_path="data", maxiter=50){
  #' Process individual accessFits for each match to id_strs.
  #'
  #' Process individual accessFits for each match to id_strs. Each fit is
  #' classified as test_type. This function is designed to make creating
  #' corrected technology fits easier.
  #'
  #' @param id_strs \emph{character array.}
  #'               Identifying character strings for sessions to process.
  #'
  #' @param test_type \emph{character.}
  #'               Type of access fit to return. Must be one of PTT, SUT, or
  #'               LEG. See \code{\link[accessTime]{accessFit}}.
  #'
  #' @param dat_path \emph{character array.}
  #'               Parent directory containg csv to use.
  #'
  #' @param maxiter \emph{numeric.}
  #'               Maximum number of iterations passed to fitting algorithm. Defaults to 50
  #'
  #' @return List of access fit objects matching \code{id_strs}.
  #'
  #' @examples
  #' # get PTT Gate fits
  #'
  #'  dat_path <- system.file("extdata", package="accessTime")
  #'  ptt_fits <- process_session_data(
  #'    "capture_PTT-gate_14-May-2021_07-30-20",
  #'    test_type = "PTT",
  #'    dat_path = dat_path
  #'    )
  #'
  #'  # Get SUT fits
  #'  sut_fits <- process_session_data(
  #'    "capture_LTE_14-Apr-2021_16-11-22",
  #'    test_type="SUT",
  #'    dat_path = dat_path
  #'  )
  #'
  #'  # Get technology fit
  #'  lte <- techFit(
  #'    sut_fits = sut_fits,
  #'    ptt_fits = ptt_fits
  #'  )
  #'
  #' @export
  # Function to load and process data for a set of tests
  # TODO: Test with ids for different tws. Also mixed setups (some encompassing ids, others not)

  # Find all session info for each id string
  sesh_info <- lapply(id_strs, find_session_csv, dat_path)

  # Extract all sessions
  all_sessions <- c(unlist(sapply(sesh_info,function(x){x[["sessions"]]})))

  # Extract all cut files
  all_cuts <- c(unlist(sapply(sesh_info,function(x){x[["cut"]]})))

  unique_sessions <- unique(all_sessions)
  unique_cuts <- unique(all_cuts)

  if(length(unique_sessions) == length(unique_cuts)){
    tw_combos <- list()
    for(k in 1:length(unique_sessions)){
      tw_combos[[k]] <- c(unique_sessions[k], unique_cuts[k])
    }
  } else{
    stop("Number of session files and cut files do not match.")
  }

  # Remove repeated sessions
  tw_fits <- lapply(
    tw_combos,
    function(x){
      process_accessData(x[1], x[2], test_type=test_type, maxiter=maxiter)
    }
    )

  # Get original talker word combinations
  tw_names_orig <- sapply(tw_fits,function(x){x[["speaker_word"]]})

  if(length(unique(tw_names_orig)) != length(tw_names_orig)){
    warning("Non-unique talker word combinations")
    # Mark duplicates
    tw_names <- tw_names_orig
    # Initialize counter for marking duplicates
    dup_count <- rep(1, length(tw_names))
    while(any(duplicated(tw_names))){
      # Find current duplicates
      dup_ix <- duplicated(tw_names)
      # Increment duplicate counter
      dup_count[dup_ix] <- dup_count[dup_ix] + 1
      # Rename with updated duplicate number
      tw_names[dup_ix] <- paste0(tw_names_orig[dup_ix], " (", dup_count[dup_ix], ")")
    }
  } else{
    tw_names <- tw_names_orig
  }

  # Name fits uniquely
  names(tw_fits) <- tw_names

  return(tw_fits)
}

#-----------------Custom Access Fit Methods-------------------------------------
eval_access <- function(accFit, alpha, sys_dly_unc=0.07/1.96*1e-3){
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
  #' @param sys_dly_unc Uncertainty of the measurement system delay. Accounts
  #'               for previous correction of PTT timing. Defaults to 0.07/2*1e-3.
  #'               This is a lower bound
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
  #' alphas <- seq(from=0.01, to=0.99, by=0.01)
  #'
  #' # Define system delay uncertainty
  #' sys_dly_unc <- 1e-3*0.07/1.96
  #'
  #' access_delays <- eval_access(analog_direct, alphas, sys_dly_unc)
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

eval_access.accessFit <- function(accFit, alpha, sys_dly_unc=0){
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
  Var_t <- C^2 * Cov["lambda", "lambda"] + Cov["t0", "t0"] + 2 * C * Cov["lambda", "t0"]

  # Get uncertainty of access time estimate
  unc <- sqrt(Var_t + sys_dly_unc^2)

  # Output list
  y<- data.frame(
    alpha=alpha,
    access_time=vals,
    uncertainty=unc
    )
  rownames(y) <- alpha
  return(y)
}

eval_intell <- function(accFit, t){
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
  #' times <- seq(from=-0.5, to=2, by=0.01)
  #'
  #' intelligibility_values <- eval_intell(analog_direct, times)
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

eval_intell.accessFit <- function(accFit, t){
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
  return(data.frame(t=t, I=y))
}

#--------------------Generic S3 Access Fit Methods------------------------------
print.accessFit <- function(x, ...){
  #' @export
  model <- x$fit$call$formula
  cat("Model:\n")
  print(model)

  coefs <- coef(x)

  cat(paste0("I0: ", coefs["I0"], "\n"))
  cat(paste0("lambda: ", coefs["lambda"], "\n"))
  cat(paste0("t0: ", coefs["t0"], "\n"))
  cat("--------------\n")
  cat(paste0("Test Type: ", x[["test_type"]], "\n"))
  cat(paste("Word(s) fit:", paste0(x$speaker_word, collapse=", "), "\n"))

}

coef.accessFit <- function(object, ...){
  #' @export
  paramCoef <- coef(object$fit)
  output <- c("I0"=object$I0, paramCoef)
  return(output)
}

confint.accessFit <- function(object, parm=NULL, level=0.95, ...){
  #' @export
  #'

  interval <- c(1,-1) * rep((1-level)/2,2) + c(0,1)
  if(is.null(parm)){
    paramInt <- confint(object$fit, level=level)
  } else{
    parmPass <- parm[parm!="I0"]
    if(length(parmPass) == 0){
      paramInt <- NULL
    } else{
      paramInt <- confint(object$fit, parm=parm, level=level)
    }
  }

  if(is.null(parm) | any(parm == "I0")){
    # Condense all P2 intelligibilities to 1D array
    dat <- object[["session_dat"]]
    R <- 1000
    if(object$test_type == "PTT"){
      p2_resamples <- sapply(
        dat,
        function(y){
          replicate(
            R,
            mean(sample(y[["PTT"]][["P2_Int"]],
              length(y[["PTT"]][["P2_Int"]]),
              replace=TRUE))
            )
        }
      )
    } else{
      p2_resamples <- sapply(
        dat,
        function(y){
          replicate(
            R,
            mean(sample(y[["SUT"]][["P2_Int"]],
              length(y[["SUT"]][["P2_Int"]]),
              replace=TRUE))
            )
        }
      )
    }

    I0_resamples <- rowMeans(p2_resamples)
    I0 <- quantile(I0_resamples,interval)
  } else{
    I0 <- NULL
  }
  output <- rbind(I0,paramInt)
  return(output)
}

vcov.accessFit <- function(object,...){
  #' @export
  return(vcov(object[["fit"]]))
}

#--------------Extra Functions--------------------------------------------------
sortSpeakers <- function(sf, ext=".csv"){
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

  bases <- basename(sf)
  noExt <- unlist(strsplit(bases, ext))
  byUnderScore <- strsplit(noExt, "_")

  N<- length(sf)
  # Preallocate arrays
  words <- vector("character", N)
  wIxs <- vector("character", N)
  bIxs <- vector("character", N)
  speakers <- vector("character", N)
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
  return(
    list(
      ordered=sf[sIx],
      speaker_word=sWord[sIx],
      order=sIx
      )
  )
}

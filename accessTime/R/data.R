# Documentation for accessTime Data sets
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
#=================ptt_gate===============================
#' accessFit Object for PTT Gate measurements
#'
#' Example access delay measurement data for a simple radio replacement,
#' known as a PTT gate.
#'
#' @format \code{\link[accessTime]{accessFit}} objects have the following
#' components:
#'
#' \describe{
#'     \item{fit}{Fit object from \code{\link[minpack.lm]{nlsLM}}. Characterizes
#'     the intelligibility and access delay curves for the system under test.}
#'     \item{I0}{Asymptotic intelligibility for the system under test.}
#'     \item{curve_dat}{
#'         A data frame with the following 3 variables: \describe{
#'             \item{t}{PTT time, in seconds. Scaled such that 0 corresponds
#'             with the start of the word under test and positive time
#'             corresponds to the amount of time between PTT being pressed and
#'             the word being spoken.}
#'             \item{I}{Intelligibility}
#'             \item{speaker}{Speaker and word combination, e.g. 'F1 hook'}}
#'     }
#'     \item{session_dat}{
#'         A list of data frames with the following 8 variables: \describe{
#'             \item{PTT_time}{PTT time in audio clip time, in seconds.
#'             Corrected for audio interface latency.}
#'             \item{PTT_start}{PTT time in audio clip time, in seconds.
#'             Uncorrected for audio interface latency.}
#'             \item{ptt_st_dly}{PTT time interval, in seconds.}
#'             \item{P1_Int}{Intelligibility of P1.}
#'             \item{P2_Int}{Intelligibility of P2.}
#'             \item{m2e_latency}{Mouth-to-ear latency estimate for the given trial.}
#'             \item{underRun}{Number of detected buffer under runs}
#'             \item{overRun}{Number of detected buffer over runs}
#'             }
#'     }
#'     \item{speaker_word}{Array of the speaker word combos used for the access
#'     delay measurement.}
#' }
"ptt_gate"

#=================analog_direct===============================
#' accessFit Object for analog direct LMR measurements
#'
#' Example access delay measurement data for a sample analog direct LMR system.
#'
#' @format \code{\link[accessTime]{accessFit}} objects have the following
#' components:
#'
#' \describe{
#'     \item{fit}{Fit object from \code{\link[minpack.lm]{nlsLM}}. Characterizes
#'     the intelligibility and access delay curves for the system under test.}
#'     \item{I0}{Asymptotic intelligibility for the system under test.}
#'     \item{curve_dat}{
#'         A data frame with the following 3 variables: \describe{
#'             \item{t}{PTT time, in seconds. Scaled such that 0 corresponds
#'             with the start of the word under test and positive time
#'             corresponds to the amount of time between PTT being pressed and
#'             the word being spoken.}
#'             \item{I}{Intelligibility}
#'             \item{speaker}{Speaker and word combination, e.g. 'F1 hook'}}
#'     }
#'     \item{session_dat}{
#'         A list of data frames with the following 8 variables: \describe{
#'             \item{PTT_time}{PTT time in audio clip time, in seconds.
#'             Corrected for audio interface latency.}
#'             \item{PTT_start}{PTT time in audio clip time, in seconds.
#'             Uncorrected for audio interface latency.}
#'             \item{ptt_st_dly}{PTT time interval, in seconds.}
#'             \item{P1_Int}{Intelligibility of P1.}
#'             \item{P2_Int}{Intelligibility of P2.}
#'             \item{m2e_latency}{Mouth-to-ear latency estimate for the given trial.}
#'             \item{underRun}{Number of detected buffer under runs}
#'             \item{overRun}{Number of detected buffer over runs}
#'             }
#'     }
#'     \item{speaker_word}{Array of the speaker word combos used for the access
#'     delay measurement.}
#' }
"analog_direct"

#=================analog_conventional===============================
#' accessFit Object for analog conventional LMR measurements
#'
#' Example access delay measurement data for a sample analog conventional LMR system.
#'
#' @format \code{\link[accessTime]{accessFit}} objects have the following
#' components:
#'
#' \describe{
#'     \item{fit}{Fit object from \code{\link[minpack.lm]{nlsLM}}. Characterizes
#'     the intelligibility and access delay curves for the system under test.}
#'     \item{I0}{Asymptotic intelligibility for the system under test.}
#'     \item{curve_dat}{
#'         A data frame with the following 3 variables: \describe{
#'             \item{t}{PTT time, in seconds. Scaled such that 0 corresponds
#'             with the start of the word under test and positive time
#'             corresponds to the amount of time between PTT being pressed and
#'             the word being spoken.}
#'             \item{I}{Intelligibility}
#'             \item{speaker}{Speaker and word combination, e.g. 'F1 hook'}}
#'     }
#'     \item{session_dat}{
#'         A list of data frames with the following 8 variables: \describe{
#'             \item{PTT_time}{PTT time in audio clip time, in seconds.
#'             Corrected for audio interface latency.}
#'             \item{PTT_start}{PTT time in audio clip time, in seconds.
#'             Uncorrected for audio interface latency.}
#'             \item{ptt_st_dly}{PTT time interval, in seconds.}
#'             \item{P1_Int}{Intelligibility of P1.}
#'             \item{P2_Int}{Intelligibility of P2.}
#'             \item{m2e_latency}{Mouth-to-ear latency estimate for the given trial.}
#'             \item{underRun}{Number of detected buffer under runs}
#'             \item{overRun}{Number of detected buffer over runs}
#'             }
#'     }
#'     \item{speaker_word}{Array of the speaker word combos used for the access
#'     delay measurement.}
#' }
"analog_conventional"

#=================p25_direct===============================
#' accessFit Object for P25 direct LMR measurements
#'
#' Example access delay measurement data for a sample P25 direct LMR system.
#'
#' @format \code{\link[accessTime]{accessFit}} objects have the following
#' components:
#'
#' \describe{
#'     \item{fit}{Fit object from \code{\link[minpack.lm]{nlsLM}}. Characterizes
#'     the intelligibility and access delay curves for the system under test.}
#'     \item{I0}{Asymptotic intelligibility for the system under test.}
#'     \item{curve_dat}{
#'         A data frame with the following 3 variables: \describe{
#'             \item{t}{PTT time, in seconds. Scaled such that 0 corresponds
#'             with the start of the word under test and positive time
#'             corresponds to the amount of time between PTT being pressed and
#'             the word being spoken.}
#'             \item{I}{Intelligibility}
#'             \item{speaker}{Speaker and word combination, e.g. 'F1 hook'}}
#'     }
#'     \item{session_dat}{
#'         A list of data frames with the following 8 variables: \describe{
#'             \item{PTT_time}{PTT time in audio clip time, in seconds.
#'             Corrected for audio interface latency.}
#'             \item{PTT_start}{PTT time in audio clip time, in seconds.
#'             Uncorrected for audio interface latency.}
#'             \item{ptt_st_dly}{PTT time interval, in seconds.}
#'             \item{P1_Int}{Intelligibility of P1.}
#'             \item{P2_Int}{Intelligibility of P2.}
#'             \item{m2e_latency}{Mouth-to-ear latency estimate for the given trial.}
#'             \item{underRun}{Number of detected buffer under runs}
#'             \item{overRun}{Number of detected buffer over runs}
#'             }
#'     }
#'     \item{speaker_word}{Array of the speaker word combos used for the access
#'     delay measurement.}
#' }
"p25_direct"

#=================p25_trunked_phase1===============================
#' accessFit Object for P25 Trunked Phase 1 LMR measurements
#'
#' Example access delay measurement data for a sample P25 Trunked Phase 1 LMR system.
#'
#' @format \code{\link[accessTime]{accessFit}} objects have the following
#' components:
#'
#' \describe{
#'     \item{fit}{Fit object from \code{\link[minpack.lm]{nlsLM}}. Characterizes
#'     the intelligibility and access delay curves for the system under test.}
#'     \item{I0}{Asymptotic intelligibility for the system under test.}
#'     \item{curve_dat}{
#'         A data frame with the following 3 variables: \describe{
#'             \item{t}{PTT time, in seconds. Scaled such that 0 corresponds
#'             with the start of the word under test and positive time
#'             corresponds to the amount of time between PTT being pressed and
#'             the word being spoken.}
#'             \item{I}{Intelligibility}
#'             \item{speaker}{Speaker and word combination, e.g. 'F1 hook'}}
#'     }
#'     \item{session_dat}{
#'         A list of data frames with the following 8 variables: \describe{
#'             \item{PTT_time}{PTT time in audio clip time, in seconds.
#'             Corrected for audio interface latency.}
#'             \item{PTT_start}{PTT time in audio clip time, in seconds.
#'             Uncorrected for audio interface latency.}
#'             \item{ptt_st_dly}{PTT time interval, in seconds.}
#'             \item{P1_Int}{Intelligibility of P1.}
#'             \item{P2_Int}{Intelligibility of P2.}
#'             \item{m2e_latency}{Mouth-to-ear latency estimate for the given trial.}
#'             \item{underRun}{Number of detected buffer under runs}
#'             \item{overRun}{Number of detected buffer over runs}
#'             }
#'     }
#'     \item{speaker_word}{Array of the speaker word combos used for the access
#'     delay measurement.}
#' }
"p25_trunked_phase1"

#=================p25_trunked_phase2===============================
#' accessFit Object for P25 Trunked Phase 2 LMR measurements
#'
#' Example access delay measurement data for a sample P25 Trunked Phase 2 LMR system.
#'
#' @format \code{\link[accessTime]{accessFit}} objects have the following
#' components:
#'
#' \describe{
#'     \item{fit}{Fit object from \code{\link[minpack.lm]{nlsLM}}. Characterizes
#'     the intelligibility and access delay curves for the system under test.}
#'     \item{I0}{Asymptotic intelligibility for the system under test.}
#'     \item{curve_dat}{
#'         A data frame with the following 3 variables: \describe{
#'             \item{t}{PTT time, in seconds. Scaled such that 0 corresponds
#'             with the start of the word under test and positive time
#'             corresponds to the amount of time between PTT being pressed and
#'             the word being spoken.}
#'             \item{I}{Intelligibility}
#'             \item{speaker}{Speaker and word combination, e.g. 'F1 hook'}}
#'     }
#'     \item{session_dat}{
#'         A list of data frames with the following 8 variables: \describe{
#'             \item{PTT_time}{PTT time in audio clip time, in seconds.
#'             Corrected for audio interface latency.}
#'             \item{PTT_start}{PTT time in audio clip time, in seconds.
#'             Uncorrected for audio interface latency.}
#'             \item{ptt_st_dly}{PTT time interval, in seconds.}
#'             \item{P1_Int}{Intelligibility of P1.}
#'             \item{P2_Int}{Intelligibility of P2.}
#'             \item{m2e_latency}{Mouth-to-ear latency estimate for the given trial.}
#'             \item{underRun}{Number of detected buffer under runs}
#'             \item{overRun}{Number of detected buffer over runs}
#'             }
#'     }
#'     \item{speaker_word}{Array of the speaker word combos used for the access
#'     delay measurement.}
#' }
"p25_trunked_phase2"

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
#' List of accessFit objects for PTT Gate measurements
#'
#' Example access delay measurement data for a simple radio replacement,
#' known as a PTT gate. Used for start of word correction via
#' \code{\link[accessTime]{techFit}}.
#'
#' This data can be easily loaded from raw data using
#' \code{\link[accessTime]{process_session_data}} with
#' \code{id_strs = "capture_PTT-gate_14-May-2021_07-30-20"}, see example.
#'
#' @format See \code{\link[accessTime]{accessFit}} documentation
#'
#' @examples
#' dat_path <- system.file("extdata", package="accessTime")
#' # Load the ptt gate data
#' ptt_gate <- process_session_data("capture_PTT-gate_14-May-2021_07-30-20","PTT",dat_path=dat_path)
#'
#' # Load data for SUT (analog direct mode here)
#' analog_direct_wut <- process_session_data("capture_Analog_12-Nov-2020_08-26-11", "SUT", dat_path=dat_path)
#' # Use the ptt gate data to generate a corrected technology fit
#' analog_direct <- techFit(analog_direct_wut,ptt_gate)
"ptt_gate"

#=================analog_direct===============================
#' accessFit Object for analog direct LMR measurements
#'
#' Example access delay measurement data for a sample analog direct LMR system.
#' Corrected fit using ptt gate for the start of word correction.
#'
#' @format See \code{\link[accessTime]{accessFit}} documentation

"analog_direct"

#=================lte=================================
#' accessFit object for an in-development LTE system measurements
#'
#' Example access delay measurement data for a sample LTE system.
#' Corrected fit using ptt gate for the start of word correction.
#'
#' @format See \code{\link[accessTime]{accessFit}} documentation
"lte"

#=================p25_direct===============================
#' accessFit Object for P25 direct LMR measurements
#'
#' Example access delay measurement data for a sample P25 direct LMR system.
#' Corrected fit using ptt gate for the start of word correction.
#'
#' @format See \code{\link[accessTime]{accessFit}} documentation
"p25_direct"

#=================p25_trunked_phase1===============================
#' accessFit Object for P25 Trunked Phase 1 LMR measurements
#'
#' Example access delay measurement data for a sample P25 Trunked Phase 1 LMR system.
#'
#' Corrected fit using ptt gate for the start of word correction.
#'
#' @format See \code{\link[accessTime]{accessFit}} documentation
"p25_trunked_phase1"

#=================p25_trunked_phase2===============================
#' accessFit Object for P25 Trunked Phase 2 LMR measurements
#'
#' Example access delay measurement data for a sample P25 Trunked Phase 2 LMR system.
#' Corrected fit using ptt gate for the start of word correction.
#'
#' @format See \code{\link[accessTime]{accessFit}} documentation
"p25_trunked_phase2"

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

#-----------------Intelligibility Plots--------------------------------
#TODO: Include examples in documentation
plot_intelligibility <- function(accFit,
                                 xlim = c(-0.6,2.5),
                                 word_curves = FALSE,
                                 title = "Intelligibility Curve",
                                 include_raw = FALSE){
  #' Plot intelligibility results
  #'
  #' Plot intelligibility results for a given access fit object. Plots the
  #' intelligibility curve, with options to plot individual words contributing
  #' to the final fit as well as the raw intelligibility data.
  #'
  #' @param accFit \emph{accessFit.}
  #'    Access fit object.
  #'
  #' @param xlim \emph{numeric.}
  #'    X-axis limits (time in seconds) for plot.
  #'
  #' @param  word_curves \emph{logical.}
  #'   Determines if word curves are plotted or not. Throws warning if
  #'   \emph{accessFit} does not have valid data for word curves
  #'   (e.g. LEG, SUT, or PTT fit).
  #'
  #' @param title \emph{character.}
  #'   Title of the plot
  #'
  #' @param  include_raw \emph{logical.}
  #'   Plot all raw intelligibility data contributing to intelligibility curve.
  #'
  #' @return \code{\link[ggplot2]{ggplot}} object.
  #'
  #' @examples
  #' # Plot intelligibility curve for LTE data
  #' plot_intelligibility(lte)
  #' # Plot intelligibility curve for LTE data with individual word curves
  #' plot_intelligibility(lte,word_curves=TRUE)
  #'
  #' # Plot intelligibility curve analog direct data with raw intelligibility points
  #' plot_intelligibility(analog_direct,include_raw = TRUE)
  #' @import ggplot2
  #' @export
  # Times to evaluate intelligibiliity
  t <- seq(from = xlim[1],to=xlim[2],by=0.01)

  #--------------Plot Raw Intell Points-------------------
  p <- ggplot()
  if(word_curves){
    if(accFit$test_type == "LEG"){
      warning("Individual word curves cannot be plotted for LEG type fits.")
    } else if(accFit$test_type == "COR"){
      # Define functino to evaluate intelligibility model
      logist_curve <- function(t,I0,t0,lambda){
        Intell <- I0/(1 + exp((t - t0)/lambda))
        return(Intell)
      }
      for(tw in accFit$speaker_word){
        cparams<- accFit$fit$orig_params$SUT[,tw]

        intell_vals <- logist_curve(t,accFit$fit$SUT_I0s[tw],cparams["t0"],cparams["lambda"])
        color_name = paste0("SUT - ", tw)
        cdf <- data.frame(t=t,I=intell_vals,speaker=color_name)


        p <- p +
          geom_line(data=cdf,aes(x=t,y=I,color=speaker),size=1.5)
      }
    }
  }

  intell <- eval_intell(accFit,t)
  color_name <- paste0(accFit$test_type, " Fitted Line")
  p <- p +
    geom_line(data=intell,aes(x=t,y=I,color=color_name),size=1.5)

  if(include_raw){
    if(accFit$test_type == "PTT"){
      # Plot PTT points only if accFit test type is PTT
      p <- base_raw_intell_plot(p, accFit,"PTT",verbose_legend = TRUE)
    } else{
      # COR, SUT, or LEG plot SUT points
      p <- base_raw_intell_plot(p,accFit,"SUT",verbose_legend = TRUE)
    }
  }
  p <- apply_intell_theme(p,xlim = xlim,title=paste0(title," - ", accFit$test_type))

  return(p)
}

# similiar to original intelligibility curves
# takes in raw (uncorrected) values
# produces raw (uncorrected) curves on plot
# word_int_curves comes from using eval_intell on individual raw words
# see example from plot_wordIntCurves in old package
plot_raw_intells <- function(accFit,
                             xlim = c(-0.6,2.5),
                             title= "Raw Intelligibilities for Select Words") {
  #' Plot raw intelligibility data
  #'
  #' Plot raw intelligibility data from an \emph{accessFit} object. For PTT or SUT
  #' type fit plots intelligibilities. For COR creates plots for PTT and SUT
  #' separately. For LEG plots SUT raw data.
  #'
  #' @param accFit \emph{accessFit.}
  #'    Access fit object.
  #'
  #' @param xlim \emph{numeric.}
  #'    X-axis limits (time in seconds) for plot.
  #'
  #' @param title \emph{character.}
  #'   Title of the plot
  #'
  #' @return \code{\link[ggplot2]{ggplot}} object.
  #' @examples
  #' plot_raw_intells(analog_direct)
  #'@importFrom ggpubr ggarrange
  #'@export


  # Check test_type, SUT and PTT make single plot, COR make two plots organized with ggarrange
  if(accFit$test_type == "COR"){
    sut_p <- base_raw_intell_plot(ggplot(),accFit,"SUT")
    sut_p <- apply_intell_theme(sut_p,xlim = xlim,title=paste0(title," - SUT"))
    ptt_p <- base_raw_intell_plot(ggplot(),accFit,"PTT")
    ptt_p <- apply_intell_theme(ptt_p,xlim = xlim,title=paste0(title," - PTT"))
    p <- ggarrange(ptt_p,sut_p,nrow = 2,ncol=1)
  } else if(accFit$test_type == "PTT"){
    p <- base_raw_intell_plot(ggplot(),accFit,"PTT")
    p <- apply_intell_theme(p,xlim = xlim,title=paste0(title," - PTT"))
  }else{
    p <- base_raw_intell_plot(ggplot(),accFit,"SUT")
    p <- apply_intell_theme(p,xlim = xlim,title=paste0(title," - ", accFit$test_type))
  }

  return(p)
}

base_raw_intell_plot <- function(p,accFit,test_type,verbose_legend = FALSE){
  #' @import ggplot2
  for(tw in accFit[["speaker_word"]]){
    cdat <- accFit[["curve_dat"]][[tw]][[test_type]]
    if(verbose_legend){
      cdat$speaker <- paste0(test_type, " - ", cdat$speaker)
    }
    p <- p + geom_point(data = cdat,aes(x=t,y=I,color=speaker))
  }

  return(p)
}

apply_intell_theme <- function(p,title,xlim = c(-0.6,2.5)){
  #' Apply intelligibility plot theme style to a ggplot object.
  #'
  #' @param p \emph{ggplot.} Plot object to apply theme to.
  #'
  #' @param title \emph{character.} Title of plot.
  #'
  #' @param xlim \emph{numeric.} Two element array defining x-axis limits.
  #'
  #' @import ggplot2

  #colorblind friendly palette
  #in order: grey, orange, pink, light blue, green, yellow, dark blue, reddish-orange, black
  color <- c("#999999", "#E69F00", "#CC79A7", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00",  "#000000")

  # Define major axis breaks for x-axis
  x_major <- round(seq(from=xlim[1], to = xlim[2], by = 0.2),1)
  y_major <- round(seq(from=0, to=1, by = 0.1),1)
  p <- p +
    # geom_point(data = accFit$curve_dat, aes(x = t, y = I, color=speaker,shape=speaker)) +
    # geom_line(data = int_curve, aes(x=t, y=I, color=speaker),  size = 1.3) +
    scale_x_continuous(breaks=x_major,limits = xlim) +
    scale_y_continuous(breaks = y_major,limits=c(0,1))+
    scale_colour_manual(values = color)+
    #could omit if the shapes makes the plot too busy
    scale_shape_manual(values = c(17, 19, 0, 4)) +
    # xlab("t [s]") + ylab("Intelligibility") + ggtitle(title) +
    theme_minimal()+
    theme(legend.title = element_blank(), plot.title = element_text(hjust = 0.5))+
    ggtitle(title)+
    xlab("t [s]")+
    ylab("Intelligibility")
  return(p)
}

#--------------------------Access Delay Plots----------------------------
plot_access <- function(...,plotlist=NULL,curve_names = NULL,title="Access Delay Curves",xlim=c(0.5,0.99),ylim=NULL,intell=FALSE,level=0.95){
  #' Plot access delay
  #'
  #' Plot access delay for \emph{accessFit} objects. Can plot multiple access
  #' delay curves at once.
  #'
  #' @param ... list of accessFit objects to plot.
  #'
  #' @param plotlist \emph{list.}
  #'   List of accessFit objects to plot access delay data for.
  #'
  #' @param curve_names \emph{character.}
  #'   Array of names for each curve. Used to label curves in plot legend.
  #'
  #' @param title \emph{character.}
  #'   Plot title.
  #'
  #' @param xlim \emph{numeric.}
  #'    X-axis limits (alpha values between 0 and 1) for plot.
  #'
  #' @param ylim \emph{numeric.}
  #'   Y-axis limits (time in seconds).
  #'
  #' @param intell \emph{logical.} Determines if x-axis is intelligibility or
  #'               alpha level.
  #'
  #' @param level \emph{numeric.} Confidence level for confidence intervals
  #'               plotted on access delay curves.Value between 0 and 1.
  #'
  #' @return \code{\link[ggplot2]{ggplot}} object.
  #' @examples
  #' # Plot access for analog direct data
  #' plot_access(analog_direct)
  #'
  #' # Plot access for P25 Phase 1 and Phase 2 Trunked, using intelligibility instead of alpha for x-axis
  #' plot_access(p25_trunked_phase1,p25_trunked_phase2,curve_names = c("Phase 1", "Phase 2"),intell = TRUE)
  #' @import ggplot2
  #' @importFrom dplyr bind_rows
  #' @export
  #'

  # Combine all fits to plot
  fits <- c(list(...),plotlist)

  # Check if curve names provided
  if(is.null(curve_names)){
    # Force all fits to have a name
    orig_names <- names(fits)
    if(is.null(orig_names)){
      # NULL if fits can't have name (one element lists apparently return this when initialized without name)
      fitnames <- "1"
    } else{
      fitnames <- orig_names
      mix <- 1
      for(ix in 1:length(orig_names)){
        # Fill in missing names
        if(orig_names[ix] == ""){
          fitnames[ix] <- paste0("Curve ", mix)
          mix <- mix + 1
        }
      }
    }
  } else{
    # Check that number of curve_names matches number of fits
    if(length(curve_names)!= length(fits)){
      stop("Number of curve names must match the number of fits")
    } else{
      fitnames <- curve_names
    }
  }
  names(fits) <- fitnames

  # Set alpha values to plot over based on xlims
  alpha_lvls <- seq(from=xlim[1],to=xlim[2],by=0.01)
  # Evaluate access
  ads <- lapply(fits,
                eval_access,
                alpha_lvls)

  # Combine into single dataframe
  access_dat <- bind_rows(ads,.id="speaker")
  if(intell){
    intell_vals <- c(sapply(fits,function(x){x$I0*alpha_lvls}))
    access_dat[["intell"]] <- intell_vals

  }
  #Remove infinit access delay values
  access_dat <- access_dat[!is.infinite(access_dat$access_time),]

  # Make plot
  if(intell){
    p <- ggplot(access_dat, aes(x=intell,y=access_time,color=speaker))
  } else{
    p <- ggplot(access_dat,aes(x=alpha,y=access_time,color=speaker))
  }
  # How much to expand uncertainty based on desired level
  K <- qnorm(1-(1-level)/2)
  p <- p +
    geom_line(size=1) +
    geom_line(aes(y=access_time+K*uncertainty, color=speaker), linetype="dashed",  size = .75) +
    geom_line(aes(y=access_time-K*uncertainty, color=speaker), linetype="dashed", size = .75) +
    theme_minimal() +
    theme(legend.title = element_blank(), plot.title = element_text(hjust = 0.5))+
    ylab("Access Delay [s]") +
    scale_x_continuous(limits=xlim)+
    ggtitle(title)
  if(intell){
    p <- p +
      xlab("Intelligibility")
  } else{
    p <- p +
      xlab(expression(alpha))
  }

  if(!is.null(ylim)){
    p <- p +
      scale_y_continuous(limits=ylim)
  }
  return(p)
}

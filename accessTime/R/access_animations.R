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


#TODO: Restore compatability with accessDelay v2.0.0

#----------------Frame Functions ----------------------
make_access_animation <- function(accFit,
                                  alpha_lvls = c(0.01,.33,.66,0.99),
                                  frame_dir = "frames",
                                  Audio_Data=NULL,
                                  output = "output.mp4",
                                  frame_rate = 10,
                                  curve_fit_audio="",
                                  video_codec = "libx264",
                                  audio_codec = "aac",
                                  tx_examples = Inf,
                                  powerpoint=FALSE,
                                  extra_settings = NULL,
                                  output_directory = ""){
  #'Create animations of access time tests
  #'
  #'Create an animation using data from \code{accFit}. Iterate through PTT
  #'times, and incrementally plot intelligibility scores. At each element of
  #'\code{alpha_lvls} specific trials will be identified that have
  #'intelligibilites close to the alpha_lvl on the intelligibility curve. If
  #'\code{Audio_Data} is passed as an argument, example recordings will also be
  #'plotted and played during the animation. Note that the accFit must be data
  #'for a single word/talker pair. Animations will not generate for accessFit
  #'objects with multiple talkers/words.
  #'
  #'@param accFit \emph{accessFit} \code{\link[accessTime]{accessFit}} object.
  #'  Note \code{accFit} must be an accessFit object for a single talker.
  #'
  #'@param alpha_lvls \emph{Numeric Vector} Fractional intelligibility levels to
  #'  show example recordings. Values must be in range (0,1). Defaults to
  #'  \code{alpha_lvls = c(0.01, 0.33, 0.66, 0.99)}.
  #'
  #'@param frame_dir \emph{character} Path where animation frames will be
  #'  stored. Defaults to \code{frame_dir = "frames"}.
  #'
  #'@param output \emph{Filename} File name of output animation. Defaults to
  #'  \code{output="output.mpg"}.
  #'
  #'@param frame_rate \emph{numeric.} Frames per second for animation.
  #'
  #'@param curve_fit_audio {character} Path to audio to play when curve fit
  #'  image is displayed.
  #'
  #'@param video_codec \emph{character} Video codec to use for output video
  #'
  #'@param audio_codec \emph{character} Audio codec to use for output video
  #'
  #'@param Audio_Data \emph{list} List with following structure: \describe{
  #'  \item{rec}{\emph{Wave} \code{\link[tuneR]{Wave-class}} object}
  #'  \item{cp}{\emph{data.frame} Data frame containing cutpoints for rec}
  #'  \item{rx_path}{\emph{character} Path where received audio files stored} }
  #'
  #'@param tx_examples \emph{numeric array.} Array containing which examples
  #'  should play but Tx and Rx audio together to demonstrate mouth-to-ear
  #'  latency. Default is \code{Inf}, which causes the last example to have both
  #'  audio files.
  #'
  #'@param powerpoint \emph{logical.} Indicator to optimize for powerpoint
  #'  presentations. Will override codec settings add some options to make the
  #'  video import into power point presentations well.
  #'
  #'@param extra_settings \emph{character.} Pass arbitrary options to ffmpeg
  #'
  #'@param output_directory \emph{character.} Directory to save intermediate
  #'  files to
  #'
  #'@details
  #'
  #'@section FFMPEG and Python: In order for the animation frames to be stitched
  #'  into a single video, both FFMPEG and Python are required to be in the
  #'  system path. If they are not in the system path, the frames will still be
  #'  generated, but the final video will not be produced and an error will be
  #'  thrown.
  #'
  #'
  #'
  #'@examples
  #' #  # Path to included raw data
  #' #  raw_path <- system.file("extdata", "Measurements", package = "accessTime")
  #' #  # Path to P25 Trunked Phase 1 Data
  #' #  test_path <- file.path(raw_path, "P25_Trunked_Phase1")
  #' #  # All files in test directory
  #' #  test_files <- list.files(test_path)
  #' #  # Select First file (F1 hook)
  #' #  test_file <- test_files[1]
  #' #  # Full path to test file
  #' #  file_path <- file.path(test_path,test_file)
  #' #
  #' #  # Directory to audio clip wav files and cut points
  #' #  cutDir <- system.file("extdata", "Audio_Clips", package="accessTime")
  #' #
  #' #  # Create access fit object
  #' #  accFit <- process_accessData(file_path,cutDir)
  #' #
  #' #  make_access_animation(accFit,
  #' #                        frame_dir="Frames-P25_Trunked_Phase1_F1_hook",
  #' #                        output="P25_Trunked_Phase1_F1_hook.mpg")

  warning("This was deprecated in accessTime v2.0.0 and likely does not work")
  print("----Making Frames----")
  # Make test frames
  make_test_frames(accFit,alpha_lvls=alpha_lvls,frame_dir=frame_dir,Audio_Data=Audio_Data)

  print("-----Stitching Frames-----")
  if(tx_examples==Inf){
    tx_examples <- length(alpha_lvls)
  }
  stitch_frames(frame_dir,output,
                frame_rate=frame_rate,
                curve_fit_audio=curve_fit_audio,
                tx_examples = tx_examples,
                powerpoint = powerpoint,
                extra_settings = extra_settings,
                output_directory=output_directory)

}

stitch_frames <- function(frame_dir,
                          output,
                          frame_rate = 10,
                          curve_fit_audio = "",
                          video_codec = "libx264",
                          audio_codec = "aac",
                          tx_examples=NULL,
                          powerpoint=FALSE,
                          extra_settings = NULL,
                          output_directory = ""){
  #'Stitch animation frames into a video file
  #'
  #'Creates an animation from frames in \code{frame_dir} and outputs video file
  #'as \code{output}.
  #'
  #'@param frame_dir \emph{character} Path where animation frames are stored.
  #'
  #'@param output \emph{character} Name of output video file.
  #'
  #'@param frame_rate \emph{numeric} Frame rate of input frames in animation.
  #'  Final output video frame rate is fixed at 30 fps. This parameter controls
  #'  how long each frame is displayed for, but does not affect final video
  #'  frame rate.
  #'
  #'@param curve_fit_audio \emph{character} Path to audio to play when curve fit
  #'  image is displayed.
  #'
  #'@param video_codec \emph{character} Video codec to use for output video
  #'
  #'@param audio_codec \emph{character} Audio codec to use for output video
  #'
  #'@param tx_examples \emph{numeric array.} Array containing which examples
  #'  should play but Tx and Rx audio together to demonstrate mouth-to-ear
  #'  latency. Default is \code{NULL}, which causes the no examples to have both
  #'  audio files.
  #'
  #'@param powerpoint \emph{logical.} Indicator to optimize for powerpoint
  #'  presentations. Will override codec settings add some options to make the
  #'  video import into power point presentations well.
  #'
  #'@param extra_settings \emph{character.} Pass arbitrary options to ffmpeg
  #'
  #'@param output_directory \emph{character.} Directory to save intermediate
  #'  files to
  #'
  #'@details
  #'
  #'@section frame_dir: The directory where the frames to put in the animation
  #'  are stored. The animation contains any number of sections where each
  #'  section contains any number of frames.
  #'
  #'  Each section has a main part and an, optional, example part. The frames in
  #'  the main part are named SectionSS_FrameFFF.png where SS is the zero padded
  #'  section number and FFF is the zero padded frame number. The example part
  #'  contains a single frame named SectionSS_Example.png where SS is the
  #'  section number. The example part also contains an audio clip named
  #'  receive_exampleSS.wav where SS is again the section number. If either the
  #'  example frame or audio is missing there is no example part.
  #'
  #'  For the end of the clip a special section is created with the frame
  #'  curve_fit.png which is shown for a duration of 1/2 a second.
  #'
  #'  Once all sections are completed they are concatinated together to create
  #'  the clip.
  #'
  #'@section FFMPEG and Python: In order for the animation frames to be stitched
  #'  into a single video, both FFMPEG and Python are required to be in the
  #'  system path. If they are not in the system path, an error will be thrown.
  #'
  #'@seealso \code{\link[accessTime]{make_access_animation}}
  #'
  #'
  warning("This was deprecated in accessTime v2.0.0 and likely does not work")
  stitch_path <- system.file("stitch.py",package="accessTime")

  # Required programs for stitch.py to function
  dependencies <- c("python","ffmpeg")
  # Locate dependencies
  dependent_locs <- Sys.which(dependencies)
  # Throw error if dependencies missing
  for(dep in dependencies){
    if(dependent_locs[dep] == ""){
      errmsg <- paste(dep, "not found in system path. It is required to stitch animation frames into a video file")
      stop(errmsg)
    }
  }
  # Create arguments list
  args_list <- c(stitch_path,
                 frame_dir,
                 "-o", output,
                 "--input-framerate", frame_rate,
                 "--video-codec", video_codec,
                 "--audio-codec", audio_codec)
  # If curve fit audio isn't empty add it
  if(curve_fit_audio != ""){
    args_list <- c(args_list,
                   "--curve-fit-audio",curve_fit_audio)
  }
  if(output_directory != ""){
    args_list <- c(args_list,
                   "--output-directory",output_directory)
    if(!file.exists(output_directory)){
      dir.create(output_directory,recursive = TRUE)
    }
  }
  if(length(tx_examples)>0){
    for(ex_i in tx_examples){
      args_list <- c(args_list,
                     "--simultaneous-tx",ex_i)
    }
  }
  if(powerpoint){
    args_list <- c(args_list,
                   "--powerPoint")
  }
  if(!is.null(extra_settings)){
    args_list <- c(args_list,
                   extra_settings)
  }

  # Call stitch.py
  stitch_response<- system2("python", args=(args_list))
  print(paste("Animation generated to:", output))
}

make_test_frames <- function(accFit,alpha_lvls = c(0.01,.33,.66,0.99),frame_dir = "frames",Audio_Data=NULL){
  #'Create animations frames of access time tests.
  #'
  #'Create an animation frames using data from \code{accFit}. Iterate through
  #'PTT times, and incrementally plot intelligibility scores. At each element of
  #'\code{alpha_lvls} specific trials will be identified that have
  #'intelligibilites close to the alpha_lvl on the intelligibility curve. If
  #'\code{Audio_Data} is passed as an argument, example recordings will also be
  #'plotted and played during the animation. Note that the animation plots data
  #'for only one talker. Note that the accFit must be data for a single
  #'word/talker pair. Animations will not generate for accessFit objects with
  #'multiple talkers/words.
  #'
  #'@param accFit \emph{accessFit} \code{\link[accessTime]{accessFit}} object.
  #'
  #'@param alpha_lvls \emph{Numeric Vector} Fractional intelligibility levels to
  #'  show example recordings. Values must be in range (0,1). Defaults to
  #'  \code{alpha_lvls = c(0.01, 0.33, 0.66, 0.99)}.
  #'
  #'@param frame_dir \emph{character} Path where animation frames will be
  #'  stored. Defaults to \code{frame_dir = "frames"}.
  #'
  #'@param Audio_Data \emph{list} List with following structure: \describe{
  #'  \item{rec}{\emph{Wave} \code{\link[tuneR]{Wave-class}} object}
  #'  \item{cp}{\emph{data.frame} Data frame containing cutpoints for rec}
  #'  \item{rx_path}{\emph{character} Path where received audio files stored} }
  #'
  #'@seealso \code{\link[accessTime]{make_access_animation}}
  #'@import ggpubr
  #'@import ggplot2
  #'

  warning("This was deprecated in accessTime v2.0.0 and likely does not work")
  # Calculate access times for different intelligibility levels
  access_data <- eval_access(accFit,alpha_lvls)

  #-------PTT Timing------
  # Find difference between ptt times
  ptt_steps <- diff(accFit$session_dat[[1]]$ptt_st_dly)
  # Calculate ptt step
  ptt_step <- -ptt_steps[ptt_steps!=0][1]
  # Get the minimum ptt
  min_ptt <- round(1e3*(min(accFit$curve_dat$t)-ptt_step))/1e3
  # Get maximum ptt
  max_ptt <- round(1e3*(max(accFit$curve_dat$t)+ptt_step))/1e3
  # Create sequence of all ptt times
  ptt_times <- seq(from=min_ptt,to=max_ptt,by=ptt_step)

  # Grab the ptt times closest to the calculated access times
  ptt_lvls_ix <- sapply(access_data$access_time, function(x){
    which.min(abs(x - ptt_times))
  })
  ptt_lvls <- ptt_times[ptt_lvls_ix]

  min_t <- round(1e3*min(accFit$curve_dat$t))/1e3
  max_t <- ceiling(1e3*max(accFit$curve_dat$t))/1e3
  x_seq <- seq(from=min_t,to=max_t,by=200e-3)

  # Make output directory to store frames if needed

  if(!file.exists(frame_dir)){
    dir.create(frame_dir,recursive=TRUE)
  } else{
    # Delete all files currently in folder
    unlink(frame_dir,recursive = TRUE)
    dir.create(frame_dir,recursive = TRUE)
  }
  section_count <- 1
  frame_count <- 1

  t_rounded <- round(accFit$curve_dat$t*1e3)/1e3

  # Get example recording indices
  recordings <- mapply(function(x,y){
    find_example_rec(session_data = accFit$curve_dat,ptt_time = x, Ival=y)
  },
  ptt_lvls,alpha_lvls,
  SIMPLIFY = FALSE)

  #-----------Recording Data Check---------------
  if(!is.null(Audio_Data)){
    # Check that the three required elements of Audio_Data are present
    flags <- vector()
    req_entries <- c("rec","cp","rx_path")
    for(entry in req_entries){
      flags[entry] <- entry %in% names(Audio_Data)
    }
    if(any(!flags)){
      missing<- which(!flags)
      err_str <- paste0("Missing entries in Audio_Data: ", paste(names(missing),collapse=", "))
      stop(err_str)
    }

    # Save transmit audio
    tx_path <- file.path(frame_dir,"Transmit.wav")
    writeWave(Audio_Data$rec,tx_path)

    # Get example recordings names
    rec_names <- sapply(recordings,function(x){x$name})
    rec_names <- paste0(rec_names,"_")

    name_parts <- strsplit(accFit$speaker_word, " ")[[1]]
    talker <- name_parts[1]
    keyword <- name_parts[2]
    rx_list <- list.files(Audio_Data$rx_path,recursive = FALSE)

    rx_ix <- sapply(rec_names,function(x){intersect(grep(talker,rx_list), intersect(grep(x,rx_list),grep(keyword,rx_list)))})
    rx_names <- sapply(rx_ix,function(x){rx_list[x]})

    full_rx_paths <- sapply(rx_names,function(x){file.path(Audio_Data$rx_path,x)})

    # Load in receive recordings
    rx_recs_raw <- lapply(full_rx_paths,readWave)
    # Grab only left channel
    rx_recs <- lapply(rx_recs_raw,function(rec){
      new_rec <- Wave(left=rec@left,
                      samp.rate = rec@samp.rate,
                      bit = rec@bit,
                      pcm = rec@pcm)
    })

    # Get max length of received audio
    rx_lens <- sapply(rx_recs,function(x){length(x)/x@samp.rate})
    max_time <- max(rx_lens)

    # Make transmit plot
    tx_plot <- Audio_Plot(Audio_Data$rec,cp=Audio_Data$cp,title="Transmit Audio",time_limit = c(0,max_time))
    # Make empty receive plot
    empty_rx <- Audio_Plot(Audio_Data$rec,title="Receive Audio",alpha=0, time_limit = c(0,max_time))

    # Example received audio ptt times
    example_ptt <- sapply(recordings,function(x){
      sum(accFit$session_dat[[1]][as.numeric(x$index),c("ptt_st_dly","m2e_latency")])
      # accFit$session_dat[[1]]$ptt_st_dly[as.numeric(x$index)]
    })
    # Make received audio example plots
    # example_plots <- lapply(rx_recs,Audio_Plot,title="Receive Audio",time_limit = c(0,max_time),color="red")

    example_plots <- mapply(function(rec,ptt_time){
      Audio_Plot(rec,PTT_time=ptt_time,title="Receive Audio",time_limit=c(0,max_time),color="red")
    },
    rx_recs,example_ptt,
    SIMPLIFY = FALSE)


    # Save out example recordings to frame directory
    zero_rx_example_counts <- formatC(1:length(rx_recs),width=2,format="d",flag="0")
    rx_out_names <- paste0("receive_example",zero_rx_example_counts,".wav")
    rx_out_paths <- file.path(frame_dir,rx_out_names)
    mapply(function(rx_rec,rx_name){
      writeWave(rx_rec,rx_name)
    }, rx_recs,rx_out_paths,
    SIMPLIFY = FALSE)

  }
  #--------------Main Loop----------------------
  rx_index <- NULL
  tx_frame_flag <- FALSE
  for(ptt_time in ptt_times){
    # Grab relevant ptt indices
    ptt_ix <- abs(t_rounded - ptt_time) < ptt_step/2
    if(any(ptt_ix)){
      # Get all indices up to current place
      all_up_to_ix <- 1:max(which(ptt_ix))
      # Subset data
      dat_subset <- accFit$curve_dat[all_up_to_ix,]

      # Make frame/section labels with leading zeros
      zero_frame_count <- formatC(frame_count, width=3, format="d",flag="0")
      zero_section_count <- formatC(section_count,width=2,format="d",flag="0")

      if(!is.null(Audio_Data) & !tx_frame_flag){
        # If on first step, make empty tx frame
        tx_frame <- make_frame(dat_subset,x_axis=x_seq,alpha=0)
        tx_frame_name <- "Transmit_frame.png"
        tx_frame_path <- file.path(frame_dir,tx_frame_name)

        tx_out_frame <- ggarrange(tx_plot,empty_rx,tx_frame,nrow=3,heights=c(1,1,3))
        # Save output frame
        ggsave(tx_frame_path,tx_out_frame,device=png(),height=9,width=8,units="in",dpi=300)
        dev.off()
        tx_frame_flag <- TRUE
      }

      print(paste0("----- Section ", section_count, " Frame ", frame_count, " ------"))
      if(any(ptt_time == ptt_lvls)){
        # **At example timestep**

        # Frame name is an example
        frame_name <- paste0("Section", zero_section_count,"_Example.png")

        # Grab recording index
        rx_index <- recordings[[which(ptt_lvls == ptt_time)]]$index
        # Make frame with example point
        frame <- make_frame(dat_subset,x_axis=x_seq,example=rx_index)

        # Reset frame count
        frame_count <- 1
        # Increment section count
        section_count <- section_count + 1

      } else{
        # Frame name
        frame_name <- paste0("Section", zero_section_count,"_Frame", zero_frame_count, ".png")
        # Make frame
        frame <- make_frame(dat_subset,x_axis=x_seq)
        # Increment frame count
        frame_count <- frame_count + 1
      }
      # Path to save frames
      frame_path <- file.path(frame_dir,frame_name)
      # Check if we have Audio Data
      if(!is.null(Audio_Data)){
        # Check if example frame
        if(!is.null(rx_index)){

          # Grab example recording plot if example frame
          ex_sub <- paste0("Rx",rx_index,"_")
          rx_plot_hold <- example_plots[[ex_sub]]
        } else{
          # Otherwise grab the empty receive plot
          rx_plot_hold <- empty_rx
        }
        # Generate full output frame
        out_frame <- ggarrange(tx_plot,rx_plot_hold,frame,nrow=3,heights=c(1,1,3))
      } else{
        out_frame <- frame
      }
      # Save output frame
      ggsave(frame_path,out_frame,device=png(),height=9,width=8,units="in",dpi=300)
      dev.off()
      # Reset receive example index
      rx_index <- NULL

    }
  }
  # Generate Intelligibility curve
  acc_coefs <- coef(accFit)
  t <- seq(min(ptt_times),max(ptt_times),0.01)
  Int <- acc_coefs["I0"]/(1 + exp((t-acc_coefs["t0"])/acc_coefs["lambda"]))
  cfit <- data.frame(t=t,I=Int)

  # make final frame with curve fit
  final_frame <- make_frame(accFit$curve_dat,x_axis = x_seq,fit = cfit)
  # Final frame path
  frame_path <- file.path(frame_dir,"curve_fit.png")
  if(!is.null(Audio_Data)){
    # Add audio plots if audio data present
    out_frame <- ggarrange(tx_plot,empty_rx,final_frame,nrow=3,heights=c(1,1,3))
  } else{
    out_frame <- final_frame
  }
  # Save final frame
  ggsave(frame_path,out_frame,device=png(),height = 9,width=8,units="in",dpi=300)
  dev.off()
}

make_frame <- function(dat_subset,x_axis=round(seq(-.6, 2, by = 0.2),1),example=FALSE,fit=NULL,alpha=1){
  #' Make access time animation frame
  #'
  #' Make single animation frame from data in \code{dat_subset}. If
  #' \code{example} is passed in, the example point is marked by a red point. If
  #' \code{fit} is passed in, it is plotted over the data points from
  #' \code{dat_subset}.
  #'
  #' @param dat_subset \emph{data.frame} Data frame containing access data to
  #'   plot. Must contain columns named \code{t} and \code{I}, representing PTT
  #'   time and intelligibility respecitively.
  #'i
  #' @param x_axis \emph{numeric vector} Breaks for x-axis (see
  #'   \code{\link[ggplot2]{scale_x_continuous}})
  #'
  #' @param example \emph{Numeric} Row number of \code{dat_subset} for the
  #'   example recording
  #'
  #' @param fit \emph{data.frame} Data frame containing curve fit data. Must
  #'   have columns named \code{t} and \code{I} representing time and
  #'   intelligibility respectively.
  #'
  #' @param alpha \emph{numeric.} Opacity of plot objects.
  #'
  #' @import ggplot2
  #'
  #'
  warning("This was deprecated in accessTime v2.0.0 and likely does not work")
  if(!(example==FALSE)){
    dat_subset$Example <- row.names(dat_subset) == example

  } else{
    dat_subset$Example <- FALSE
  }

  cur_time <- max(dat_subset$t)
  g <- ggplot(dat_subset,aes(x=t,y=I))+
    geom_point(color="black",alpha=alpha)+
    geom_vline(xintercept=cur_time,color="black",alpha=0.7)+
    geom_point(data = subset(dat_subset, Example != FALSE),color="red",size= 5)
  if(!is.null(fit)){
    # Plot fit line
    g <- g +
      geom_line(data=fit,aes(x=t,y=I),color="red",size=2)
  }
  g <- g +
    theme(legend.title = element_blank(), plot.title = element_text(hjust = 0.5)) +
    xlab("t [s]") + ylab("Intelligibility") +
    scale_colour_manual(values = c("grey3","red"))+
    scale_x_continuous(breaks = x_axis,limits = c(min(x_axis),max(x_axis))) +
    scale_y_continuous(breaks = round(seq(0, 1, by = 0.1),1),limits=c(0,1))
  return(g)
}

find_example_rec <- function(session_data,ptt_time,Ival,ptt_step=20e-3){
  #' Find example recordings in access time data
  #'
  #' Search \code{session_data} for an example recording at a given PTT time
  #' that has P1 intelligibility close to \code{Ival}.
  #'
  #' @param session_data \emph{data.frame} Data frame for access time test
  #'
  #' @param ptt_time \emph{numeric scalar} PTT time to search around
  #'
  #' @param Ival \emph{numeric scalar} Intelligibility value (0<\code{Ival}<1)
  #'   that example P1 should be near
  #'
  #' @param ptt_step \emph{numeric scalar} PTT time increment for given test.
  #'
  #'
  #'
  warning("This was deprecated in accessTime v2.0.0 and likely does not work")
  ptt_times <- round(session_data$t*1e3)/1e3
  ptt_ix <- abs(ptt_times - ptt_time) < ptt_step/2
  sd_sub <- session_data[ptt_ix,]
  rx_ix <- which.min(abs(sd_sub$I - Ival))
  rx_label <- row.names(sd_sub[rx_ix,])
  rx_name <- paste0("Rx",rx_label)
  return(list(index=rx_label,
              name= rx_name)
  )
}

Audio_Plot <- function(rec,cp=NULL,PTT_time=NULL,title="Audio",alpha=1,time_limit=NULL,color="black"){
  #' Plot recording audio
  #'
  #' Plot audio data in \code{rec}. If cutpoints passed in via \code{cp}, then
  #' P1 will be identified by a gray rectangle around it.
  #'
  #' @param rec \emph{Wave} \code{\link[tuneR]{Wave-class}} object containing
  #'   recording data.
  #'
  #' @param cp \emph{data.frame} Data frame containing cutpoints for rec
  #'
  #' @param PTT_time \emph{numeric scalar} Value at which vertical, black,
  #'   dotted line will be plotted to designate PTT being pressed.
  #'
  #' @param time_limit \emph{numeric vector} Two element vector containing
  #'   limits for x-axis. See \code{\link[ggplot2]{scale_x_continuous}}.
  #'
  #' @param PTT_time \emph{numeric scalar} Value at which vertical, black,
  #'   dotted line will be plotted to designate PTT being pressed.
  #'
  #' @param title \emph{character} Title for audio plot
  #'
  #' @param alpha \emph{numeric scalar} Value between 0 and 1 for opacity of
  #'   audio
  #'
  #' @param color \emph{character} Color for audio plot.
  #' @import ggplot2
  #'
  #' @export


  if(!is.null(cp)){
    # If cutpoints supplied find P1 start and end
    p1_start <- cp[2,"Start"]/rec@samp.rate
    p1_end <- cp[2,"End"]/rec@samp.rate
  }

  # Grab data from left channel
  x <- rec@left
  # Time vector
  time <- (1:length(x))/rec@samp.rate
  # Recording data frame of audio data and time
  rec_df <- data.frame(t=time,w=x)

  if(is.null(time_limit)){
    # If no time_limit supplied set to [0, max_time]
    max_time <- max(time)
    time_limit <- c(0,max_time)
  }

  # Make recording plot
  rec_plot <- ggplot(rec_df,aes(x=t,y=w))
  # If cutpoint make gray rectangle around P1
  if(!is.null(cp)){
    rec_plot <- rec_plot+
      annotate("rect",xmin=p1_start,xmax=p1_end,ymin=-Inf,ymax=Inf,alpha=0.2)
  }

  rec_plot <- rec_plot +
    geom_line(alpha=alpha,color=color)
  if(!is.null(PTT_time)){
    rec_plot <- rec_plot +
      geom_vline(xintercept = PTT_time,linetype="dashed")
  }
  rec_plot <- rec_plot +
    scale_x_continuous(limits=time_limit)+
    theme_minimal()+
    theme(axis.title.y=element_blank(),
          axis.text.y=element_blank(),
          axis.ticks.y=element_blank())+
    xlab("Time [s]")+
    ggtitle(title)

  return(rec_plot)
}



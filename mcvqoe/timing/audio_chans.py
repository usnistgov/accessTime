

def require_timecode(audio_player):
    """
    Throw error if a timecode will not be recorded.

    This function is used to make sure that a timecode will be recorded for
    a two location test.

    Raises
    ------
    ValueError
        If there are no timecode channels

    See Also
    --------
    mcvqoe.mouth2ear : Two location m2e tests use timecodes.

    Examples
    --------

    By default there is no timecode recorded by AudioPlayer.

    >>> ap=AudioPlayer()
    >>> ap.require_timecode()
    ValueError: Timecode channel not found in ('rx_voice',)

    If a timecode is recorded, no error is raised.
    >>> ap=AudioPlayer(rec_chans={'rx_voice':0,'IRIGB_timecode':1})
    >>> ap.require_timecode()

    """
    
    for chan in audio_player.rec_chans:
        if 'timecode' in chan:
            #found! we are done
            break
    else:
        #not found, raise error
        chans=tuple(audio_player.rec_chans.keys())
        raise ValueError(f'Timecode channel not found in {chans}')
        

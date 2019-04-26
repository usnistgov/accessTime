% funciton Vol_Search(varargin)
%Vol_Search Read in desired search parameters, such as a radio type, audio
%clip name, or both. Searches the database for the ideal volume settings
%and prints out values related to the input parameters.
%
% Vol_Search(name, value) Possible name value pairs are shown below:
%
% NAME          TYPE            Description
% 
% Radio_Type    string          Desired radio type
%
% Audio_Name    string          Desired audio clip
%

%% Input parsing
% Create input parser
p = inputParser();

% Optional radio type parameter
addParameter(p,'Radio_Type',[],@(d)validateattributes(d,{'char','string'},{'scalartext'}));
% Optional audio file name parameter
addParameter(p,'Audio_Name',[],@(d)validateattributes(d,{'char','string'},{'scalartext'}));

parse(p,varargin{:});
% Check for radio type input
if p.results.Radio_Type == 1
    Radio_Type = p.results.Radio_Type;
else 
    Radio_Type = 'All';
end    
% Check for audio clip name input
if p.results.Audio_Name == 1
    Audio_Name = p.results.Audio_Name;
else
    Audio_Name = 'All';
end    
%% Search database for Vtx and Vrx settings for given input
Database = csvread
%% Find desired information from database
%% Print found information
% 
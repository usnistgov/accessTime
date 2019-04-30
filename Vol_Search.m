function [Results] = Vol_Search(varargin)
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

% Load radio type input
Radio_Type = p.Results.Radio_Type;  
% Load audio clip name input
Audio_Name = p.Results.Audio_Name;

%Load database file
Database = readtable('O:\Users\cjg2\VolumeSettingsDatabase.csv');
Database(21:end,:) = [];
Database = table2cell(Database);
%% Search database for Vtx and Vrx settings for given input
%Check through input conditions. For those conditions, print the found
%results
if (strcmp(Audio_Name, 'all') == true) && (strcmp(Radio_Type, 'all') == true)
    Results = Database(:,:);
elseif (strcmp(Audio_Name, 'all') == true) 
    Radio_Spec = (strcmp(Database(:,:),Radio_Type) == true);
    Results = Database(Radio_Spec,:);
elseif (strcmp(Radio_Type, 'all') == true)
    Audio_Spec = (strcmp(Database(:,:),Audio_Name) == true);
    %Debug here%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    Results = Database(:,Audio_Spec);
%Case where both are not all    
end    

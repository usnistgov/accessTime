function Vol_Search(varargin)
%Vol_Search Read in desired search parameters, such as a radio type, audio
%clip name, or both. Searches the database for the ideal volume settings
%and prints out values related to the input parameters.
%
% Vol_Search(name, value) Possible name value pairs are shown below:
%
% NAME          TYPE            Description
% 
% Radio_Type    string          Desired radio type. For any, enter 'all'.
%
% Audio_Name    string          Desired audio clip.For any, enter 'all'.
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

% Load database file
% Turn off table variable name warning 
warning('off','all')
fname = 'VolumeSettingsDatabase.csv';
ddir = fullfile('..','log-search');
Data = readtable(fullfile(ddir,fname));
Data(21:end,:) = [];
Database = table2cell(Data);
Headings = {'Radio' 'Audio' 'Vtx' ' Vrx'};

%% Search database for Vtx and Vrx settings for given input
% Check through input conditions. For those conditions, print the found
% results

% Both conditions are 'all'
if (strcmp(Audio_Name, 'all') == true) && (strcmp(Radio_Type, 'all') == true)
    % Print the full database
    Results = cell2table(Database(:,:), 'VariableNames', Headings)
    
% Audio name is all, radio type is specific   
elseif (strcmp(Audio_Name, 'all') == true) 
    Radio_Spec = (strcmp(Database(:,:),Radio_Type) == true);
    % Print results
    Results = cell2table(Database(Radio_Spec,:), 'VariableNames', Headings)
    
% Radio type is all, audio name is specific    
elseif (strcmp(Radio_Type, 'all') == true)
    Audio_Spec = (strcmp(Database(:,:),Audio_Name) == true);
    for n = 1:length(Database)    
        if Audio_Spec(n,2) == true
            Audio_Spec(n,1) = 1;
            Audio_Spec(n,2) = 0;
        end     
    end    
   % Print results
   Results = cell2table(Database(Audio_Spec,:), 'VariableNames', Headings)
   
% Case where both are not all, are specific
elseif (strcmp(Audio_Name, 'all') == false) && (strcmp(Radio_Type, 'all') == false)
    Spec_R = (strcmp(Database(:,:),Radio_Type) == true);
    Spec_A = (strcmp(Database(:,:),Audio_Name) == true);
    Spec = logical(Spec_R + Spec_A); 
    for k = 1:length(Database)
        if Spec(k,2) == true & Spec(k,1) == true
            Spec(k,1) = 1;
        else Spec(k,1) = 0 ;   
        end  
    end    
    Spec(:,2) = 0;
    % Print results
    Results = cell2table(Database(Spec,:), 'VariableNames', Headings)
end    
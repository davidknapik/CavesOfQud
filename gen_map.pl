#!/usr/bin/perl

use Time::Piece;

# Init Zone hash
# $zone{zone_loc}{NAME} = "City Name" ;
# $zone{zone_loc}{COLOR} = color code/#xxxxxx ;
# $zone{zone_loc}{CURRENT} = 1 ;
my %zone = ();

# caves of qud save location & specific game save location
my $savedir = "C:\\Users\\owner\\AppData\\LocalLow\\Freehold\ Games\\CavesOfQud";
my $saveUID = "0469531a-048d-4549-b26d-88034706eeac";

# output file
my $html_file = 'parsang_map.html';

# csv list of cities (in Save Dir)
my $locations_csv = 'cities.csv';


###############################################################################
# main loop
###############################################################################

# &read_cache_dir();

while(1) {

    my $current_modified = (stat $savedir . "\\Player.log")[9];

    if( $current_modified-$prev_modified > 15 ) {

        print("Detected file change...Regenerating map $current_modified\n");

        &read_player_log();

#        &add_locations();

        &gen_html_output();

        $prev_modified = $current_modified;

    };

    # limit disk thrashing
    sleep(10);

}

exit ;


###############################################################################
# Subs
###############################################################################

###############################################################################
# Read filenames in zone cache dir
# Add locatioin to zone hash
# Set any visited locations to lightgrey
###############################################################################
sub read_cache_dir() {

    my $zone_cache_dir = $savedir . "\\Saves\\$saveUID\\ZoneCache";

    # read zone cache dir
    opendir(CACHEDIR,$zone_cache_dir) || die "Can't opendir $zone_cache_dir: $!";
        my @zonecache = readdir(CACHEDIR);
    close CACHEDIR;

    foreach(@zonecache) {
        $_ =~ s/JoppaWorld\.//g;
        $_ =~ s/\.zone\.gz//g;
        # print("$_\n");
        $zone{$_}{COLOR} = 'lightgrey';
    }

}

###############################################################################
# Parse Player.log file
# Look for zones that are Thawing/Building
# Set any found locations to grey
# Set last found location to CURRENT
###############################################################################
sub read_player_log(){
    # Read current Player.log
    # tail -n 1000 -f Player.log | awk -F. '/INFO - Thawing|INFO - Building/{print $2 "." $4 " " $3 "." $5 " :" 10-$6}' 
    my $player_log_file = $savedir . "\\Player.log";

    # unset old CURRENT
    foreach $loc (keys %zone) {
        if (exists $zone{$loc}{CURRENT}){
            delete $zone{$loc}{CURRENT} ;
        }
    }

    open(PLAYERLOG, "<", $player_log_file) || die "Can't open file $player_log_file: $!";
        while(<PLAYERLOG>){
            if($_ =~ m/INFO - Finished \'Thawing|INFO - Finished \'Building/){
                $_ =~ /(\d+.\d+.\d+.\d+.\d+)/;
                $current_location=$1;
                $zone{$1}{COLOR} = 'grey';
            }
        }

        # Set the last read location as Current: color magenta
        $zone{$current_location}{COLOR} = 'magenta';
        $zone{$current_location}{CURRENT} = 1 ;

	printf("Current Location: %s\n",$current_location);
    close(PLAYERLOG);

}

###############################################################################
# Add city/sites of discovered locations
# Read file with found cities
#
# City list format (Location, Color, Name)
#  11.22.1.1.10,#554f97,Joppa
#
#  ?TODO? Need to parse Prmary.sav and pull locations from there
###############################################################################
sub add_locations() {

    my $filename = $savedir . "\\" . $locations_csv ;

    open(FH, "<", $filename) || die "Can't open file $filename: $!";

    while(<FH>){
        # ($loc, $color, $name) = split(/,/,$_);

        next unless ($_ =~ /^(\d{1,2}\.\d{1,2}\.\d\.\d\.\d{1,2}),(.+),(.+)$/ ) ;
        $zone{&trim($1)}{NAME} = &trim($3) ;
        $zone{&trim($1)}{COLOR} = &trim($2);
    }

    close(FH) ;

}


#
# Write HTML File
#
sub gen_html_output(){
    open(HTMLOUT, '>', $html_file) or die $!;

    &gen_html_header(); 
    &gen_html_table();
    &gen_html_footer();

    close(HTMLOUT);
}

#
# Trim leading/trailing spaces from string
#
sub  trim { my $s = shift; $s =~ s/^\s+|\s+$//g; return $s };

sub gen_html_header() {

    print HTMLOUT ("<!DOCTYPE html>\n");
    print HTMLOUT ("<html>\n");
    print HTMLOUT ("<head>\n");

    print HTMLOUT ("\t<title>CavesOfQud Parsang Map</title>\n");
    print HTMLOUT ("\t<meta http-equiv=\"refresh\" content=\"30\">\n");

    print HTMLOUT ("\t<style>\n");
    print HTMLOUT ("\t\ttable {\n");
    print HTMLOUT ("\t\t\tfont-family: arial, sans-serif;\n");
    print HTMLOUT ("\t\t\tborder-collapse: collapse;\n");
    print HTMLOUT ("\t\t\twidth: 100%;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\tth {\n");
    print HTMLOUT ("\t\t\tbackground-color: lightslategrey;\n");
    print HTMLOUT ("\t\t\tborder: 4px solid #d70513;\n");
    print HTMLOUT ("\t\t\tposition: sticky;\n");
    print HTMLOUT ("\t\t\ttop: 0;\n");
    print HTMLOUT ("\t\t\tleft: 0;\n");
    print HTMLOUT ("\t\t\ttext-align: center;\n");
    print HTMLOUT ("\t\t\tpadding: 8px;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttd {\n");
    print HTMLOUT ("\t\t\tborder: 1px solid #dddddd;\n");
    print HTMLOUT ("\t\t\ttext-align: center;\n");
    print HTMLOUT ("\t\t\ttext-overflow: ellipsis;\n");
    print HTMLOUT ("\t\t\tpadding: 8px;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttr.border-bottom {\n");
    print HTMLOUT ("\t\t\tborder-bottom: solid 4px #d70513;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttr.border-top {\n");
    print HTMLOUT ("\t\t\tborder-top: solid 4px #d70513;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttd.border-left {\n");
    print HTMLOUT ("\t\t\tborder-left: solid 4px #d70513;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttd.border-right {\n");
    print HTMLOUT ("\t\t\tborder-right: solid 4px #d70513;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttd.border-top {\n");
    print HTMLOUT ("\t\t\tborder-top: solid 4px #d70513;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttd.border-bottom {\n");
    print HTMLOUT ("\t\t\tborder-bottom: solid 4px #d70513;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t\ttd.current-location {\n");
    print HTMLOUT ("\t\t\tborder: solid 8px #f817d6;\n");
    print HTMLOUT ("\t\t}\n");

    print HTMLOUT ("\t</style>\n");
    print HTMLOUT ("</head>\n");

    print HTMLOUT ("\n");

}


sub gen_html_table($) {

    my $tr_class;
    my $td_class;
    my $td_bgcolor;
    my $td_str;
    my $zone_depth = 10 ; 

    print HTMLOUT ("<body>\n");
    print HTMLOUT ("\t<center><h1>Caves Of Qud Parsang Map</h1></center>\n");

    printf HTMLOUT ("Generated: %s\n", localtime->datetime);

    print HTMLOUT ("\t<table>\n");

    # output map header
    print HTMLOUT ("\t\t<tr>\n");
    print HTMLOUT ("\t\t\t<th>&nbsp;</th>");
    for ( my $parsang_x = 0; $parsang_x < 80; $parsang_x++) {
        for ( my$zone_x = 0; $zone_x <= 2; $zone_x++) {
            printf HTMLOUT ("<th>%s.%s</th>",$parsang_x,$zone_x);
        }
    }
    print HTMLOUT ("\n");

    # output map data
    for ( my $parsang_y = 0; $parsang_y < 25; $parsang_y++) {
        for ( my $zone_y = 0; $zone_y <= 2; $zone_y++) {

            # draw border for the 3x3 grid
            if ($zone_y == 0) {
                $tr_class = "class=\"border-top\"" ;
            } else {
                $tr_class = "" ;
            }

            # open data row
            printf HTMLOUT ("\t\t<tr %s>\n", $tr_class);

            # output row index
            printf HTMLOUT ("\t\t\t<th>%s.%s</th>",$parsang_y, $zone_y);

            # output row data
            for ( $parsang_x = 0; $parsang_x < 80; $parsang_x++ ) {
                for ( $zone_x = 0; $zone_x <= 2; $zone_x++) {

                    # set border based on column
                    if ( $zone_x == 0 ) {
                        $td_class = "class=\"border-left\"" ; 
                    } else {
                        $td_class = "" ; 
                    }

                    # set bgcolor if visited
                    # $zone{'1.1.1.1.10'}{'visited'} = 'color spec';
                    my $zone_loc = join('.',$parsang_x,$parsang_y,$zone_x,$zone_y,$zone_depth);
                    # print("$zone_loc\n");

                    # populate City locations
                    if ( exists($zone{$zone_loc}{NAME})) {
                        $td_str = $zone{$zone_loc}{NAME} ;
                    } else {
                        $td_str = '&nbsp;' ;
                    }

                    # show current location
                    if ( exists($zone{$zone_loc}{COLOR})) {
                        if (exists($zone{$zone_loc}{CURRENT})) {
                            $td_class = "class=\"current-location\"" ;
                            # $td_str = "$parsang_x.$zone_x $parsang_y.$zone_y" if $td_str == '&nbsp;';
                        }
                        $td_bgcolor = "bgcolor=" . $zone{$zone_loc}{COLOR} ;
                    } else {
                        $td_bgcolor = '' ;
                    }

                    printf HTMLOUT ("<td %s %s>%s</td>", $td_class, $td_bgcolor, $td_str);
                }
            }
            printf HTMLOUT ("\n");

            # end data row
            print HTMLOUT ("\t\t</tr>\n");
            printf HTMLOUT ("\n");
        }
    }

    printf HTMLOUT ("\n");

    print HTMLOUT ("\t</table>\n");
    print HTMLOUT ("</body>\n");

    print HTMLOUT ("\n");

}


sub gen_html_footer() {

    print HTMLOUT ("</html>\n");
    print HTMLOUT ("\n");

}

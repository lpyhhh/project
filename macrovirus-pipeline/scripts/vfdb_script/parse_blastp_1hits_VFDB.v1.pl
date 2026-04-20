#!/usr/bin/perl
use strict;
use Bio::SearchIO;
die "Usage:  $0 output.blast > besthit.tab \n" if(@ARGV != 1);

my $file = shift @ARGV;
my $in = Bio::SearchIO->new(-format => 'blast',
                            -file    => $file);

print "Query\tQuery_function\tSubject\tQueryLen\tSubjectLen\tAlignmentLen\tQuerycov \(\%\)\tSubjectcov \(\%\)\tE_value\tIdentity \(\%\)\tSimilarity \(\%\)\tSymbol\tFunction\tVirulence factor\tVFDB ID\tSource species\n";

my $count = 0;
my $number = 0;
my $symbol = '';
my $subjectdes = '';
my $virulence = '';
my $vfdb = '';
my $species = '';

while( my $r = $in->next_result ) {          #read a result
    $count = 0;
    $number++;
    if ($r->num_hits < 1){
        print $r->query_name,"\t","No hit\n";
        next;
    }
    while( my $h = $r->next_hit ) {            #read a hit

    #warn " Hit is ", $h->name, " Hit raw scores ", $h->raw_score, " Hit Len is ", $h->length, " aa\n";
    #>gb|ADN32826.1| BUN24p41.8 [Bacteroides uniformis]
        my $hitlen = $h->length;
        while( my $hsp = $h->next_hsp ) {
            my $subjectname = $h->name;
            $subjectname =~ s/\(.*?\)//g;
              
            my $querycover = ($hsp->length('query'))/$r->query_length * 100;
            $querycover = sprintf("%.1f",$querycover);
            my $subjectcover = ($hsp->length('hit'))/$h->length * 100;
            $subjectcover = sprintf("%.1f",$subjectcover);
            my $identity = $hsp->frac_identical('total');
            $identity = sprintf("%.1f", $identity*100);
            my $similarity = $hsp->frac_conserved('total');
            $similarity = sprintf("%.1f", $similarity*100);
            my $alignment = $hsp->length('total');
            my $desc = $h->description;
            #warn $r->query_name, "\t$desc\n";
            #> VFG013503(gi:30995470) (lsgA) lipopolysaccharide biosynthesis 
            #transporter [LOS (CVF494)] [Haemophilus influenzae Rd KW20]
            #if ($desc =~ /^(\S+)\s+(.*?)\s*\[(.*)\s+\((.*?)\)\]\s*\[(.*?)\]/){
            if ($desc =~ /^(\S+)\s+(.*?)\s*\[(.*?)\]\s*\[(.*?)\]/) {
                $symbol = $1;
                $subjectdes = $2;
                my $temp_vf = $3;
                $species = $4;
                my @aaa;
                if ($temp_vf=~/\s/) {
                    @aaa = split /\s+/, $temp_vf;
                } else {
                    @aaa = split /\(/, $temp_vf;
                }
                $vfdb = pop(@aaa);
                $virulence = join(" ", @aaa);
                if ($vfdb =~ /(\S+)\((.*)\)$/) {
                    $virulence = $virulence . " " . $1;
                    $vfdb = $2;
                } else {
                    $vfdb =~ s/^\(//g;
                    $vfdb =~ s/\)$//g;
                }
                $symbol =~ s/^\(//g;
                $symbol =~ s/\)$//g;
                if ($count < 1){
                    print $r->query_name,"\t", $r->query_description,"\t", $subjectname, "\t",$r->query_length,"\t",$h->length,"\t",$alignment,"\t",
                        $querycover,"\t",$subjectcover,"\t",$hsp->evalue,"\t",$identity,"\t", $similarity, "\t",
                        $symbol,"\t",$subjectdes, "\t", $virulence, "\t", $vfdb, "\t", $species, "\n";
                    $count++;
                }
            }
            
            last;
        }    
    }
}
#warn "$number\n";

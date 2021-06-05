
import click
import configparser

@click.command()
@click.option('-y', '--year', 'year', default = 2013, help = "ERFS-FPR year", show_default = True,
    type = int, required = True)
@click.option('-c', '--configfile', default = None,
    help = 'raw_data.ini path to read years to process.', show_default = True)
def main(year=2014, configfile = None):
    print(year, configfile)
    years = []
    if configfile is not None:
        try:
            config = configparser.ConfigParser()
            config.read(configfile)
            for key in config['erfs_fpr']:
                if key.isnumeric():
                    years.append(int(key))
                    print(f"Adding year {int(key)}")
        except KeyError:
            years = [year]
            print(f"File {configfile} not found, switchin to default {years}")
    else:
        years = [year]
    for year in years:
        print(f'aggregates{year}.csv')

if __name__ == '__main__':
    main()
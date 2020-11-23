from configparser import ConfigParser


def config(filename='database.ini', section='postgresql'):
    """ Reads the configuration for the passed filename and section """
    parser = ConfigParser()
    parser.read(filename)

    # Get the section
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db
